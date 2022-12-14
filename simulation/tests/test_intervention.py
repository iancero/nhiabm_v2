import copy
import random
from intervention import (
    Intervention,
    MockInterventionA,
    MockInterventionB,
    NetworkIntervention,
    IndividualIntervention,
)
import igraph as ig
from agent import Agent


class TestIntervention:
    def test_init_(self):
        params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**params)

        hasattr(intv, "intv_class_name")
        hasattr(intv, "start_tick")
        hasattr(intv, "duration")
        hasattr(intv, "tar_severity")
        hasattr(intv, "p_rewire")
        hasattr(intv, "p_enrolled")
        hasattr(intv, "p_beh_change")

        assert intv.last_tick == 7

    def test_is_active_phase(self):
        params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**params)

        assert not intv.is_active_phase(t=4)
        assert intv.is_active_phase(t=6)
        assert not intv.is_active_phase(t=10)

    def test_is_setup_phase(self):
        params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**params)

        assert not intv.is_setup_phase(t=4)
        assert intv.is_setup_phase(t=5)
        assert intv.is_active_phase(t=6)
        assert not intv.is_active_phase(t=8)

    def test_setup(self):

        intv_params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**intv_params)
        agents = [Agent(id=i, n_beh=3) for i in range(4)]

        correct_enrollment = ["id_0", "id_1", "id_2", "id_3"]

        world_params = {
            "sui_ORs": [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8],
            "random_param1": 23,
            "random_param2": 24,
        }

        intv.setup(agents=agents, network="placeholder", **world_params)

        assert intv.sui_ORs == world_params["sui_ORs"]
        assert intv.random_param1 == world_params["random_param1"]
        assert intv.random_param2 == world_params["random_param2"]

        assert intv.enrolled_names == correct_enrollment

    def test_risk_factor_ranks(self):
        intv_params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**intv_params)

        risk_ORs = [2.2, 1.1, 4.4, 3.3]
        assert intv.risk_factor_ranks(risk_ORs) == [1, 0, 3, 2]

        # Does it break ties in the order they are discovered
        risk_ORs = [3, 2, 3, 3]
        assert intv.risk_factor_ranks(risk_ORs) == [1, 0, 2, 3]

    def test_target_behaviors(self):
        intv_params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**intv_params)

        risk_ORs = [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8]
        assert intv.target_behaviors(risk_ORs, tar_severity=[0.50, 0.75]) == [4, 5]

        # Can it handle ties in risk factors?
        risk_ORs = [2, 3, 3, 3]
        assert intv.target_behaviors(risk_ORs, tar_severity=[0.33, 1]) == [1, 2, 3]

    def test_enrolled_agents(self):
        intv_params = {
            "intv_class_name": "Intervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = Intervention(**intv_params)

        agents = [Agent(id=i, n_beh=3) for i in range(4)]
        intv.enrolled_names = ["id_1", "id_2"]

        enrolled = intv.enrolled_agents(agents)
        enrolled_names = [e.name for e in enrolled]

        assert set(intv.enrolled_names) == set(enrolled_names)


class TestNetworkIntervention:
    def test_setup(self):
        intv_params = {
            "intv_class_name": "NetworkIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = NetworkIntervention(**intv_params)

        # A lot of agents to ensure we can test enrollment statistically below
        agents = [Agent(id=i, n_beh=3) for i in range(100)]

        world_params = {
            "sui_ORs": [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8],
        }

        intv.setup(agents=agents, network="placeholder", **world_params)

        assert intv.sui_ORs == world_params["sui_ORs"]
        assert intv.tar_severity == intv_params["tar_severity"]
        assert intv.tar_beh
        assert all([i in [4, 5] for i in intv.tar_beh])

        # Should enroll about 50% of the 100 agents
        assert (25 < len(intv.enrolled_names)) & (len(intv.enrolled_names) < 75)

    def test_intervene(self):
        # Network
        network = ig.Graph.Erdos_Renyi(n=20, p=0.50)

        # Agents
        agents = []
        for i, v in enumerate(network.vs):
            agent = Agent(id=i, n_beh=32)

            # Vertex and agent must have same name
            v["name"] = agent.name

            agents.append(agent)

        # Intervention
        intv_params = {
            "intv_class_name": "NetworkIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = NetworkIntervention(**intv_params)

        world_params = {"sui_ORs": random.sample(range(2, 50), 32)}

        intv.setup(agents=agents, network="placeholder", **world_params)

        old_es = [e.tuple for e in network.es]
        old_agents = copy.deepcopy(agents)

        intv.intervene(agents, network)

        new_es = [e.tuple for e in network.es]

        # Some edges should be rewired, but probably not all
        matching_edges = [old == new for old, new in zip(old_es, new_es)]
        assert any(matching_edges)
        assert not all(matching_edges)

        # Calculate all the changes produced by intv and where they occured
        tar_changes = []
        untar_changes = []
        for old, new in zip(old_agents, agents):
            for i, beh_pair in enumerate(zip(old.beh, new.beh)):

                # Changes we expect to sometimes see because they are targeted
                if i in intv.tar_beh:
                    tar_changes.append(beh_pair[1] - beh_pair[0])

                # Changes we expect never to see because they are untargeted
                else:
                    untar_changes.append(beh_pair[1] - beh_pair[0])

        # at least some changes, and all were for the better
        assert tar_changes
        assert any(tar_changes)
        assert all([change <= 0 for change in tar_changes])

        # no untargeted changes
        assert untar_changes
        assert not any(untar_changes)


class TestIndividualIntervention:
    def test_prioritize_agents(self):
        intv_params = {
            "intv_class_name": "IndividualIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = IndividualIntervention(**intv_params)

        agents = [Agent(id=i, n_beh=3) for i in range(4)]

        world_params = {
            "sui_ORs": [2, 2, 11, 3, 3],  # 1 really high risk and 4 small ones
        }

        agents[1].beh = [0, 0, 0, 0, 0]  # lowest risk
        agents[0].beh = [1, 1, 0, 0, 0]  # second lowest risk
        agents[3].beh = [1, 1, 0, 1, 1]  # third_lowest risk
        agents[2].beh = [0, 0, 1, 0, 0]  # highest risk because of 1 big factor

        correct_order = ["id_2", "id_3", "id_0", "id_1"]

        unranked_names = [a.name for a in agents]

        ranked_agents = intv.prioritize_agents(agents, world_params["sui_ORs"])

        assert ranked_agents

        ranked_names = [a.name for a in ranked_agents]

        assert unranked_names != ranked_names
        assert ranked_names == correct_order

    def test_treatable_behaviors(self):
        intv_params = {
            "intv_class_name": "IndividualIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = IndividualIntervention(**intv_params)

        risk_ORs = [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8]
        assert intv.treatable_behaviors(risk_ORs, tar_severity=[0.50, 0.75]) == 2

        # Can it handle ties in risk factors?
        risk_ORs = [2, 3, 3, 3]
        assert intv.treatable_behaviors(risk_ORs, tar_severity=[0.33, 1]) == 3

    def test_setup(self):
        intv_params = {
            "intv_class_name": "IndividualIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.40, 1],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = IndividualIntervention(**intv_params)

        agents = [Agent(id=i, n_beh=3) for i in range(4)]

        world_params = {
            "sui_ORs": [2, 2, 11, 3, 3],  # 1 really high risk and 4 small ones
        }

        agents[1].beh = [0, 0, 0, 0, 0]  # lowest risk
        agents[0].beh = [1, 1, 0, 0, 0]  # second lowest risk
        agents[3].beh = [1, 1, 0, 1, 1]  # third_lowest risk
        agents[2].beh = [0, 0, 1, 0, 0]  # highest risk because of 1 big factor

        correct_enrollment = ["id_2", "id_3"]

        intv.setup(agents=agents, network="placeholder", **world_params)

        assert intv.treatable_beh == 3
        assert intv.enrolled_names == correct_enrollment

    def test_priority_behaviors(self):
        intv_params = {
            "intv_class_name": "IndividualIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = IndividualIntervention(**intv_params)

        agent = Agent(id=0, n_beh=5)

        intv.sui_ORs = [2, 12, 11, 3, 3]

        agent.beh = [1, 0, 1, 1, 1]  # highest risk factor not active

        correct_priorities = [2, 4, 3, 0]

        assert intv.priority_behaviors(agent) == correct_priorities

    def test_intervene(self):

        # Network
        network = ig.Graph.Erdos_Renyi(n=4, p=0.50)

        # Agents
        agents = []
        for i, v in enumerate(network.vs):
            agent = Agent(id=i, n_beh=5)

            # Vertex and agent must have same name
            v["name"] = agent.name

            agents.append(agent)

        agents[1].beh = [0, 0, 0, 0, 0, 0]  # lowest risk
        agents[0].beh = [1, 1, 0, 0, 0, 0]  # second lowest risk
        agents[3].beh = [1, 1, 0, 1, 1, 1]  # third_lowest risk (enrolled)
        agents[2].beh = [0, 1, 1, 1, 1, 1]  # highest risk (enrolled)

        # Intervention
        intv_params = {
            "intv_class_name": "IndividualIntervention",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.25, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = IndividualIntervention(**intv_params)

        world_params = {
            "sui_ORs": [2, 12, 11, 3, 3, 3],
        }

        intv.setup(agents=agents, network=network, **world_params)

        old_es = [e.tuple for e in network.es]
        old_agents = copy.deepcopy(agents)

        intv.intervene(agents, network)

        new_es = [e.tuple for e in network.es]

        # no rewiring should occur for individual intervention
        matching_edges = [old == new for old, new in zip(old_es, new_es)]
        assert all(matching_edges)

        # Calculate all the changes produced by intv and where they occured
        tar_changes = []
        untar_changes = []
        for old, new in zip(old_agents, agents):
            for i, beh_pair in enumerate(zip(old.beh, new.beh)):

                # Changes we expect to sometimes see because they are targeted
                if old.name in intv.enrolled_names:
                    tar_changes.append(beh_pair[1] - beh_pair[0])

                # Changes we expect never to see because they are untargeted
                else:
                    untar_changes.append(beh_pair[1] - beh_pair[0])

        # at least some changes, and all were for the better
        assert tar_changes
        assert any(tar_changes)
        assert not all(tar_changes)
        assert all([change <= 0 for change in tar_changes])

        # no untargeted changes
        assert untar_changes
        assert not any(untar_changes)


class TestMockInterventionA:
    def test_setup(self):
        intv_params = {
            "intv_class_name": "MockInterventionA",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = MockInterventionA(**intv_params)

        # A lot of agents to ensure we can test enrollment statistically below
        agents = [Agent(id=i, n_beh=3) for i in range(100)]

        world_params = {
            "sui_ORs": [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8],
        }

        intv.setup(agents=agents, network="placeholder", **world_params)

        assert intv.sui_ORs == world_params["sui_ORs"]
        assert intv.tar_severity == intv_params["tar_severity"]
        assert intv.tar_beh
        assert all([i in [4, 5] for i in intv.tar_beh])

        # Should enroll about 50% of the 100 agents
        assert (25 < len(intv.enrolled_names)) & (len(intv.enrolled_names) < 75)

    def test_intervene(self):
        # Network
        network = ig.Graph.Erdos_Renyi(n=20, p=0.50)

        # Agents
        agents = []
        for i, v in enumerate(network.vs):
            agent = Agent(id=i, n_beh=32)

            # Vertex and agent must have same name
            v["name"] = agent.name

            agents.append(agent)

        # Intervention
        intv_params = {
            "intv_class_name": "MockInterventionA",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.50,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = MockInterventionA(**intv_params)

        world_params = {"sui_ORs": random.sample(range(2, 50), 32)}

        intv.setup(agents=agents, network="placeholder", **world_params)

        old_es = [e.tuple for e in network.es]
        old_agents = copy.deepcopy(agents)

        intv.intervene(agents, network)

        new_es = [e.tuple for e in network.es]

        # No edges should be changed
        assert new_es
        assert set(old_es) == set(new_es)

        # Calculate all the changes produced by intv and where they occured
        tar_changes = []
        untar_changes = []
        for old, new in zip(old_agents, agents):
            for i, beh_pair in enumerate(zip(old.beh, new.beh)):

                # Changes we expect to sometimes see because they are targeted
                if i in intv.tar_beh:
                    tar_changes.append(beh_pair[1] - beh_pair[0])

                # Changes we expect never to see because they are untargeted
                else:
                    untar_changes.append(beh_pair[1] - beh_pair[0])

        # at least some changes, and all were for the better
        assert tar_changes
        assert any(tar_changes)
        assert all([change in [-1, 0, 1] for change in tar_changes])

        # no untargeted changes
        assert untar_changes
        assert not any(untar_changes)


class TestMockInterventionB:
    def test_setup(self):
        intv_params = {
            "intv_class_name": "MockInterventionB",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.25,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = MockInterventionB(**intv_params)

        # A lot of agents to ensure we can test enrollment statistically below
        agents = [Agent(id=i, n_beh=3) for i in range(100)]

        world_params = {
            "sui_ORs": [2.2, 1.1, 4.4, 3.3, 5.5, 6.6, 7.7, 8.8],
        }

        intv.setup(agents=agents, network="placeholder", **world_params)

        assert intv.sui_ORs == world_params["sui_ORs"]
        assert intv.tar_severity == intv_params["tar_severity"]
        assert intv.tar_beh
        assert all([i in [4, 5] for i in intv.tar_beh])

        # Should enroll about 50% of the 100 agents
        assert (25 < len(intv.enrolled_names)) & (len(intv.enrolled_names) < 75)

    def test_intervene(self):
        # Network
        network = ig.Graph.Erdos_Renyi(n=20, p=0.50)

        # Agents
        agents = []
        for i, v in enumerate(network.vs):
            agent = Agent(id=i, n_beh=32)

            # Vertex and agent must have same name
            v["name"] = agent.name

            agents.append(agent)

        # Intervention
        intv_params = {
            "intv_class_name": "MockInterventionB",
            "start_tick": 5,
            "duration": 3,
            "tar_severity": [0.50, 0.75],
            "p_rewire": 0.50,
            "p_enrolled": 0.50,
            "p_beh_change": 0.50,
        }

        intv = MockInterventionB(**intv_params)

        world_params = {"sui_ORs": random.sample(range(2, 50), 32)}

        intv.setup(agents=agents, network="placeholder", **world_params)

        old_es = [e.tuple for e in network.es]
        old_agents = copy.deepcopy(agents)

        intv.intervene(agents, network)

        new_es = [e.tuple for e in network.es]

        # Some edges should be removed, but not all
        assert new_es
        assert len(new_es) < len(old_es)

        # Calculate all the changes produced by intv and where they occured
        tar_changes = []
        untar_changes = []
        for old, new in zip(old_agents, agents):
            for i, beh_pair in enumerate(zip(old.beh, new.beh)):

                # Changes we expect to sometimes see because they are targeted
                if i in intv.tar_beh:
                    tar_changes.append(beh_pair[1] - beh_pair[0])

                # Changes we expect never to see because they are untargeted
                else:
                    untar_changes.append(beh_pair[1] - beh_pair[0])

        # at least some changes, and all were for the better
        assert tar_changes
        assert any(tar_changes)
        assert all([change in [-1, 0, 1] for change in tar_changes])

        # no untargeted changes
        assert untar_changes
        assert not any(untar_changes)
