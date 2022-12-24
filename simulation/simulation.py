import copy
import json
import random
import igraph as ig

from itertools import chain

from intervention import (
    NetworkIntervention,
    IndividualIntervention,
    MockInterventionA,
    MockInterventionB,
)
from agent import Agent


class Simulation:
    def __init__(self, ticks, **kwargs):

        self.__dict__.update(kwargs)
        self.total_ticks = ticks
        self.cur_tick = 0
        self.history = {
            "agents": [],
            "edges": [],
            "vertices": [],
            "networks": [],
            "interventions": [],
            "parameters": [],
        }

    def setup(self):

        # Network
        self.network = ig.Graph.Erdos_Renyi(
            n=self.n_agents, p=self.p_edge, directed=False, loops=False
        )

        # Agents
        self.agents = []
        for i, v in enumerate(self.network.vs):
            agent = Agent(id=i, n_beh=self.n_beh)

            # Vertex and agent must have same name
            v["name"] = agent.name

            self.agents.append(agent)

        # Interventions
        self.interventions = []
        for intv_params in self.intervention_params:
            intv_class = globals()[intv_params["intv_class_name"]]
            intv = intv_class(**intv_params)
            self.interventions.append(intv)

        self.validate()

        self.record_history()

    def tick(self):

        self.validate()

        random.shuffle(self.agents)

        # (A) Conduct any interventions
        for intv in self.interventions:
            if intv.is_setup_phase(self.cur_tick):
                intv.setup(self.agents, self.network, sui_ORs=self.sui_ORs)

            if intv.is_active_phase(self.cur_tick):
                intv.intervene(self.agents, self.network)

        # (B) Agents interact with each other and world
        for i, agent in enumerate(self.agents):

            # (1) Emulate alters
            self.agents[i].emulate_alters(
                agents=self.agents, network=self.network, p=self.p_emul
            )

            # (2) Prune old, dissimilar alters
            self.agents[i].prune_alters(
                agents=self.agents, network=self.network, sim_thresh=self.sim_thresh
            )

            # (3) Recruit new, more similar alters
            self.agents[i].recruit_alters(
                agents=self.agents, network=self.network, sim_thresh=self.sim_thresh
            )

            # (4) Spontaneously change in favor of baserates
            self.agents[i].spontaneously_change(
                baserates=self.baserates, susceptibility=self.p_spon_change
            )

            # (5) Consider whether to attempt suicide
            self.agents[i].consider_suicide(
                odds_ratios=self.sui_ORs,
                gen_sui_prev=self.gen_sui_prev,
                gen_ave_beh=self.gen_ave_beh,
            )

        self.validate()

        self.record_history()

        self.cur_tick = self.cur_tick + 1

    def go(self):
        self.validate()

        while self.cur_tick < self.total_ticks:
            self.tick()

        self.validate()

    def validate(self):

        # No extra / missing agents or vertices
        agent_names = [a.name for a in self.agents]
        vertex_names = [v["name"] for v in self.network.vs]
        assert set(agent_names) == set(vertex_names)

        assert self.n_beh == len(self.agents[0].beh)
        assert self.n_beh == len(self.sui_ORs)
        assert self.n_beh == len(self.baserates)

        for intv in self.interventions:
            assert intv.start_tick <= self.total_ticks
            assert (intv.start_tick + intv.duration - 1) <= self.total_ticks

        return True

    def agents_to_dict(self):
        agent_dicts = [a.as_dict() for a in self.agents]

        return agent_dicts

    def edges_to_dict(self):
        edges = []
        for edge in self.network.es:
            edges.append(
                {
                    "src_index": edge.source,
                    "src_name": edge.source_vertex["name"],
                    "tar_index": edge.target,
                    "tar_name": edge.target_vertex["name"],
                }
            )

        return edges

    def verts_to_dict(self):
        verts = []
        for vert in self.network.vs:
            verts.append({"index": vert.index, "name": vert["name"]})

        return verts

    def interventions_to_dict(self):
        intv_dicts = []
        for intv in self.interventions:
            intv_dict = intv.as_dict()
            intv_dicts.append(intv_dict)

        return intv_dicts

    def params_to_dict(self, flat=True, in_list=True):
        params = copy.deepcopy(self.__dict__)

        non_params = ["network", "agents", "interventions", "history"]
        params = {key: val for key, val in params.items() if key not in non_params}

        intv_params = params.pop("intervention_params")[0]

        if flat:
            listlike_params = ["tar_severity"]
            for listlike in listlike_params:
                for i, item in enumerate(intv_params.pop(listlike)):
                    intv_params.update({f"{listlike}{i}": item})

            listlike_params = ["sui_ORs", "baserates"]
            for listlike in listlike_params:
                for i, item in enumerate(params.pop(listlike)):
                    params.update({f"{listlike}{i}": item})

        params.update(intv_params)

        if in_list:
            params = [params]

        return params

    def network_to_dict(self, in_list=True):
        d = {}

        d.update({"density": self.network.density()})

        # individual assortativities
        for i in range(self.n_beh):
            agent_behs = [a.beh[i] for a in self.agents]
            assort = self.network.assortativity(types1=agent_behs, directed=False)
            d.update({f"assort_beh{i}": assort})

        beh_sums = [sum(a.beh) for a in self.agents]
        d["assort_sum_beh"] = self.network.assortativity(
            types1=beh_sums, directed=False
        )

        cur_risks = [a.current_risk for a in self.agents]
        d["assort_cur_risk"] = self.network.assortativity(
            types1=cur_risks, directed=False
        )

        if in_list:
            d = [d]

        return d

    # def record_history(self):

    #     self.history["agents"].append(copy.deepcopy(self.agents_to_dict()))
    #     self.history["edges"].append(copy.deepcopy(self.edges_to_dict()))
    #     self.history["vertices"].append(copy.deepcopy(self.verts_to_dict()))
    #     self.history["networks"].append(copy.deepcopy(self.network_to_dict()))
    #     self.history["interventions"].append(
    #         copy.deepcopy(self.interventions_to_dict())
    #     )
    #     self.history["parameters"].append(copy.deepcopy(self.params_to_dict()))

    def record_history(self):

        self.history["agents"].append(self.agents_to_dict())
        self.history["edges"].append(self.edges_to_dict())
        # self.history["vertices"].append(self.verts_to_dict())
        self.history["networks"].append(self.network_to_dict())
        self.history["interventions"].append(self.interventions_to_dict())

        if self.cur_tick <= 1:
            self.history["parameters"].append(self.params_to_dict())

    def tag_history(self):

        # Go through each kind of history. Within each kind of history,
        # tag all of the individual items with the correct tick and with the
        # sim_id for this simulation, which can be used to uniquely identify it

        for aspect in self.history:
            for i, objs in enumerate(self.history[aspect]):
                for obj in objs:
                    obj.update({"tick": i, "sim_id": self.sim_id})

    def history_to_db(self, con, history_of=None, simplify=True):
        if history_of is None:
            history_aspects = ["agents", "edges", "parameters"]
        else:
            history_aspects = history_of

        for history_aspect in history_aspects:
            history = self.history_to_dataframe(history_aspect)
            # history["seed"] = self.seed
            history["sample_num"] = self.sample_num

            if simplify and history_aspect == "parameters":
                history = history.iloc[[0]]

            history.to_sql(history_aspect, con, if_exists="append", index=False)

    def history_for_db(self, simplify=True):
        self.tag_history()

        exportable_history = {}
        for history_of in [
            "agents",
            "edges",
            "parameters",
            "networks",
            "interventions",
        ]:
            flat_history = list(chain.from_iterable(self.history[history_of]))
            exportable_history[history_of] = flat_history

        if simplify:
            exportable_history["parameters"] = [exportable_history["parameters"][0]]

        return exportable_history


if __name__ == "__main__":
    from main import run_simulation

    x = run_simulation(1)
