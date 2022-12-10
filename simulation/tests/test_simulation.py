import copy
from agent import Agent
from simulation import Simulation


class TestSimulation:
    def test_init(self):
        params = {"ticks": 10, "n_beh": 10}
        s = Simulation(**params)

        assert isinstance(s, Simulation)
        assert hasattr(s, "n_beh")
        assert s.n_beh == 10
        assert s.total_ticks == 10
        assert s.cur_tick == 0

        assert hasattr(s, "history")
        assert isinstance(s.history, list)

    def test_setup(self):
        params = {
            "ticks": 10,
            "n_agents": 10,
            "n_beh": 3,
            "n_interactions": 3,
            "baserates": [0.50, 0.50, 0.50],
            "sui_ORs": [2, 3, 4],
            "p_edge": 0.50,
            "p_spon_change": 0.50,
            "sim_thresh": 0.50,
            "intervention_params": [
                {
                    "intv_class_name": "NetworkIntervention",
                    "start_tick": 10,
                    "duration": 1,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 0.50,
                    "p_beh_change": 0.50,
                },
                {
                    "intv_class_name": "IndividualIntervention",
                    "start_tick": 10,
                    "duration": 1,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 0.50,
                    "p_beh_change": 0.50,
                },
            ],
        }

        sim = Simulation(**params)
        assert not hasattr(sim, "network")
        assert not hasattr(sim, "agents")
        assert isinstance(sim.history, list)
        assert not sim.history

        sim.setup()
        assert sim.network
        assert sim.agents
        assert len(sim.network.vs) == params["n_agents"]
        assert all([len(a.beh) == params["n_beh"] for a in sim.agents])

        agent_names = [a.name for a in sim.agents]
        assert all([a_name in sim.network.vs["name"] for a_name in agent_names])
        assert all([v["name"] in agent_names for i, v in enumerate(sim.network.vs)])

        intervention_classes = [intv.__class__.__name__ for intv in sim.interventions]
        assert intervention_classes == ["NetworkIntervention", "IndividualIntervention"]
        assert sim.interventions[0].tar_severity == [0.40, 1]
        assert sim.interventions[1].tar_severity == [0.40, 1]

        assert len(sim.history) == 1

    def test_tick(self):
        params = {
            "ticks": 30,
            "n_agents": 10,
            "n_beh": 3,
            "n_interactions": 3,
            "baserates": [0.50, 0.50, 0.50],
            "sui_ORs": [2, 3, 4],
            "p_edge": 0.50,
            "p_emul": 0.50,
            "p_spon_change": 0.50,
            "sim_thresh": 0.50,
            "gen_sui_prev": 1 / 100,
            "gen_ave_beh": 0,
            "intervention_params": [
                {
                    "intv_class_name": "NetworkIntervention",
                    "start_tick": 2,
                    "duration": 1,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 1,
                    "p_beh_change": 1,
                },
                {
                    "intv_class_name": "IndividualIntervention",
                    "start_tick": 2,
                    "duration": 1,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 1,
                    "p_beh_change": 1,
                },
            ],
        }

        sim = Simulation(**params)

        assert not sim.history

        sim.setup()

        assert sim.cur_tick == 0
        assert len(sim.history) == 1
        for intv in sim.interventions:
            assert not intv.is_active_phase(sim.cur_tick)
            assert not intv.is_setup_phase(sim.cur_tick)

        old_agents = copy.deepcopy(sim.agents)
        old_network = copy.deepcopy(sim.network)

        sim.tick()
        assert sim.cur_tick == 1
        assert len(sim.history) == 2
        for intv in sim.interventions:
            assert not intv.is_active_phase(sim.cur_tick)
            assert not intv.is_setup_phase(sim.cur_tick)

        sim.tick()
        assert sim.cur_tick == 2
        assert len(sim.history) == 3
        for intv in sim.interventions:
            assert intv.is_active_phase(sim.cur_tick)
            assert intv.is_setup_phase(sim.cur_tick)

        sim.tick()
        assert sim.cur_tick == 3
        assert len(sim.history) == 4
        for intv in sim.interventions:
            assert not intv.is_active_phase(sim.cur_tick)
            assert not intv.is_setup_phase(sim.cur_tick)

        agent_changes = []
        for old, new in zip(old_agents, sim.agents):
            changes = any([old_b != new_b for old_b, new_b in zip(old.beh, new.beh)])
            agent_changes.append(changes)

        assert any(agent_changes)

        old_edges = [e.tuple for e in old_network.es]
        new_edges = [e.tuple for e in sim.network.es]
        assert not all([old == new for old, new in zip(old_edges, new_edges)])

        old_verts = [v["name"] for v in old_network.vs]
        new_verts = [v["name"] for v in sim.network.vs]
        assert set(old_verts) == set(new_verts)

    def test_go(self):
        params = {
            "ticks": 30,
            "n_agents": 10,
            "n_beh": 3,
            "n_interactions": 3,
            "baserates": [0.50, 0.50, 0.50],
            "sui_ORs": [2, 3, 4],
            "p_edge": 0.50,
            "p_emul": 0.50,
            "p_spon_change": 0.50,
            "sim_thresh": 0.50,
            "gen_sui_prev": 1 / 100,
            "gen_ave_beh": 0,
            "intervention_params": [
                {
                    "intv_class_name": "NetworkIntervention",
                    "start_tick": 15,
                    "duration": 3,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 1,
                    "p_beh_change": 1,
                },
                {
                    "intv_class_name": "IndividualIntervention",
                    "start_tick": 20,
                    "duration": 5,
                    "tar_severity": [0.40, 1],
                    "p_rewire": 0.25,
                    "p_enrolled": 1,
                    "p_beh_change": 1,
                },
            ],
        }

        sim = Simulation(**params)

        assert not sim.history

        sim.setup()

        assert len(sim.history) == 1

        sim.go()

        # number of ticks from params, plus 1 for setup
        assert len(sim.history) == 31
