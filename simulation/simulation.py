import copy
import itertools
import json
import random
import igraph as ig
from intervention import NetworkIntervention, IndividualIntervention
from agent import Agent


class Simulation:
    def __init__(self, ticks, **kwargs):

        self.__dict__.update(kwargs)
        self.total_ticks = ticks
        self.cur_tick = 0
        self.history = []

    def setup(self):

        # Network
        self.network = ig.Graph.Erdos_Renyi(
            n=self.n_agents, p=self.p_edge, directed=False, loops=False
        )

        # Agents
        self.agents = []
        for i, v in enumerate(self.network.vs):
            agent = Agent(id=i, n_beh=self.n_beh, max_alters=v.degree())

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
                odds_ratios=self.sui_ORs, gen_sui_prev=self.gen_sui_prev
            )

        self.validate()

        self.record_history()

        self.cur_tick = self.cur_tick + 1

    def go(self, ticks=10):
        for t in itertools.repeat(None, ticks):
            self.tick()

        self.validate()

    def validate(self):

        # No extra / missing agents or vertices
        agent_names = [a.name for a in self.agents]
        vertex_names = [v["name"] for v in self.network.vs]
        assert set(agent_names) == set(vertex_names)

        assert len(self.sui_ORs) == len(self.agents[0].beh)

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

    def record_history(self):
        a = copy.deepcopy(self.agents_to_dict())
        e = copy.deepcopy(self.edges_to_dict())
        v = copy.deepcopy(self.verts_to_dict())

        self.history.append({"agents": a, "edges": e, "vertices": v})

    def remaining_ticks(self):
        return self.total_ticks - self.cur_tick

    def write_json(self, file_name):
        with open(file_name, "w") as outfile:
            history_json = json.dumps(self.history)
            outfile.write(history_json)
