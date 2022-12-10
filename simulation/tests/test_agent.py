from math import exp
import igraph as ig
from agent import Agent


class TestAgent:
    def test_init(self):
        a = Agent(id=1, n_beh=100, n_interactions=3, baserates=None)
        assert (0 < sum(a.beh)) and (sum(a.beh) < 100)

        assert isinstance(a, Agent)
        assert hasattr(a, "id")
        assert hasattr(a, "name")
        assert hasattr(a, "beh")
        assert hasattr(a, "n_interactions")
        assert hasattr(a, "attempts")

        assert a.name == "id_1"
        assert a.attempts == 0
        assert isinstance(a.id, int)
        assert isinstance(a.beh, list)
        assert isinstance(a.n_interactions, int)

        b = Agent(id=2, n_beh=3, n_interactions=3, baserates=[0, 0, 0])
        assert sum(b.beh) == 0

        c = Agent(id=3, n_beh=3, n_interactions=3, baserates=[1, 1, 1])
        assert sum(c.beh) == 3

        d = Agent(id=4, n_beh=100, n_interactions=3, baserates=[0.25] * 100)
        assert (0 < sum(d.beh)) and (sum(d.beh) < 50)

    def test_emulate(self):
        a = Agent(id=1, n_beh=3, n_interactions=3)
        a.beh = [0, 0, 0]

        b = Agent(id=2, n_beh=3, n_interactions=3)
        b.beh = [1, 1, 1]

        c = Agent(id=3, n_beh=3, n_interactions=3)
        c.beh = [0, 1, 0]

        assert a.beh == [0, 0, 0]

        a.emulate(b, p=0)
        assert a.beh == [0, 0, 0]

        a.emulate(b, p=1)
        assert a.beh == [1, 1, 1]

        a.emulate(c, p=1)
        assert a.beh == [0, 1, 0]

    def test_emulate_alters(self):
        a = Agent(id=1, n_beh=3, n_interactions=3)
        a.beh = [0, 0, 0]

        b = Agent(id=2, n_beh=3, n_interactions=3)
        b.beh = [1, 1, 1]

        c = Agent(id=3, n_beh=3, n_interactions=3)
        c.beh = [2, 2, 2]  # normally impossible, but helps for testing

        d = Agent(id=4, n_beh=3, n_interactions=3)
        d.beh = [-1, -1, -1]  # normally impossible, but helps for testing

        agents = [a, b, c, d]
        net = ig.Graph(edges=[(0, 1), (0, 2), (3, 4), (2, 4)])
        net.vs["name"] = [f"id_{agent.id}" for agent in agents]

        # should choose one person from b and c to perfectly emulate
        a.n_interactions = 1
        a.emulate_alters(agents, net, p=1)
        assert (a.beh == [1, 1, 1]) or (a.beh == [2, 2, 2])

        # should repeatedly emulate b and c until all original 0's are replaced
        a.beh = [0, 0, 0]
        a.n_interactions = 20
        a.emulate_alters(agents, net, p=0.50)
        assert all([b > 0 for b in a.beh])

        # should attempt to emulate b, then c, with p = 0, so should not change
        d.n_interactions = 5
        d.emulate_alters(agents, net, p=0)
        # assert d.beh == [0, 0, 0]

    def test_spontaneously_change(self):
        a = Agent(id=1, n_beh=3, n_interactions=3)
        a.beh = [0, 0, 0]

        baserates = [1, 1, 1]
        a.spontaneously_change(baserates, susceptibility=1)
        assert a.beh == [1, 1, 1]

        baserates = [0, 0, 0]
        a.spontaneously_change(baserates, susceptibility=1)
        assert a.beh == [0, 0, 0]

        baserates = [0, 1, 0]
        a.spontaneously_change(baserates, susceptibility=1)
        assert a.beh == [0, 1, 0]

        baserates = [1, 1, 1]
        a.spontaneously_change(baserates, susceptibility=0)
        assert a.beh == [0, 1, 0]

    def test_network_index(self):
        a = Agent(id=1, n_beh=3, n_interactions=3)
        b = Agent(id=2, n_beh=3, n_interactions=3)  # connected
        c = Agent(id=3, n_beh=3, n_interactions=3)
        agents = [a, b, c]

        net = ig.Graph(edges=[(0, 1), (0, 2), (1, 3), (1, 4)])
        net.vs["name"] = [f"id_{agent.id}" for agent in agents]

        assert a.network_index(net) == 0
        assert b.network_index(net) == 1
        assert c.network_index(net) == 2

        # Now the vertext indices of this new network are different, so the
        # previous equivalence between the network and agent lists is unreliable.
        # The network_index() method should still work, despite this problem
        net2 = net.induced_subgraph(vertices=[1, 2])

        assert a.name not in net2.vs["name"]
        assert net2.vs[0]["name"] == b.name
        assert net2.vs[1]["name"] == c.name
        assert b.network_index(net2) == 0
        assert c.network_index(net2) == 1

    def test_alters(self):

        # Intentionally complicated ids to ensure alters can be retrieved,
        # even when agent ids don't directly corrospond to network.vs indices
        a = Agent(id=1010, n_beh=3, n_interactions=3)
        b = Agent(id=232, n_beh=3, n_interactions=3)  # connected
        c = Agent(id=35432, n_beh=3, n_interactions=3)  # connected
        d = Agent(id=44124, n_beh=3, n_interactions=3)  # not connected
        e = Agent(id=44, n_beh=3, n_interactions=3)  # not connected
        agents = [a, b, c, d, e]

        net = ig.Graph(edges=[(0, 1), (0, 2), (1, 3), (1, 4), (4, 5)])
        net.vs["name"] = [f"id_{agent.id}" for agent in agents]

        # Shuffling agents so the are intentionally out of order with network.vs
        # vertex order
        agents = [c, b, a, e, d]
        print(net.vs["name"])

        # should retrieve b and c, but not d and e
        alters = a.alters(agents=agents, network=net)
        assert alters
        assert isinstance(alters, list)
        assert len(alters) == 2
        assert b in alters
        assert c in alters
        assert d not in alters
        assert e not in alters

        # No valid alters, return empty list
        alters = a.alters(agents=[d, e], network=net)
        assert not alters
        assert isinstance(alters, list)

        # Not agents given, return empty list
        alters = a.alters(agents=[], network=net)
        assert isinstance(alters, list)
        assert not alters

    def test_recruit_alters(self):
        # Intentionally odd IDs, to ensure method works when orderly IDs cant
        # be relied on
        a = Agent(id=33, n_beh=3, n_interactions=3)
        a.beh = [1, 1, 1]

        # 66% similar (should recruit when thresh = .50)
        b = Agent(id=101, n_beh=3, n_interactions=3)
        b.beh = [1, 1, 0]

        # only 33% similar (should not recruit, whem thresh = .50)
        c = Agent(id=123, n_beh=3, n_interactions=3)
        c.beh = [1, 0, 0]

        agents = [a, b, c]

        # desired connection between a and b is intentionally missing
        net = ig.Graph(edges=[(1, 2)])
        net.vs["name"] = [f"id_{agent.id}" for agent in agents]

        # Use vertex names, no edge attributes
        edges = [(e.source_vertex["name"], e.target_vertex["name"]) for e in net.es]
        assert ("id_33", "id_101") not in edges  # not connected yet
        assert ("id_33", "id_123") not in edges
        assert ("id_101", "id_123") in edges

        # with this sim_thresh, b should be recruited, but no one else
        a.recruit_alters(agents, net, sim_thresh=0.50)

        # Use vertex names, no edge attributes
        edges = [(e.source_vertex["name"], e.target_vertex["name"]) for e in net.es]
        assert ("id_33", "id_101") in edges  # connected now
        assert ("id_33", "id_123") not in edges
        assert ("id_101", "id_123") in edges

    def test_prune_alters(self):
        # Intentionally odd IDs, to ensure method works when orderly IDs cant
        # be relied on
        a = Agent(id=33, n_beh=3, n_interactions=3)
        a.beh = [1, 1, 1]

        # 66% similar (should NOT prune when thresh = .50)
        b = Agent(id=101, n_beh=3, n_interactions=3)
        b.beh = [1, 1, 0]

        # only 33% similar (should prune, whem thresh = .50)
        c = Agent(id=123, n_beh=3, n_interactions=3)
        c.beh = [1, 0, 0]

        agents = [a, b, c]
        # complete network
        net = ig.Graph(edges=[(0, 1), (0, 2), (1, 2)])
        net.vs["name"] = [f"id_{agent.id}" for agent in agents]

        # Use vertex names, no edge attributes
        edges = [(e.source_vertex["name"], e.target_vertex["name"]) for e in net.es]
        assert ("id_33", "id_101") in edges
        assert ("id_33", "id_123") in edges
        assert ("id_101", "id_123") in edges

        # with this sim_thresh b should be retained, but c should be pruned
        a.prune_alters(agents, net, sim_thresh=0.50)

        edges = [(e.source_vertex["name"], e.target_vertex["name"]) for e in net.es]
        assert ("id_33", "id_101") in edges  # should be retained
        assert ("id_33", "id_123") not in edges  # should now be gone
        assert ("id_101", "id_123") in edges  # should be totally unaffected

    def test_suicide_risk(self):

        a = Agent(id=1, n_beh=3, n_interactions=3, baserates=None)

        gen_sui_prev = 1 / 100
        beh_odds_ratios = [2, 3, 4]

        a.beh = [0, 0, 0]
        p = a.suicide_risk(odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev)
        assert round(p, 4) == round(gen_sui_prev, 4)

        a.beh = [1, 0, 0]
        p = a.suicide_risk(odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev)
        a_odds = p / (1 - p)
        general_odds = gen_sui_prev / (1 - gen_sui_prev)
        a_odds_ratio = a_odds / general_odds
        assert round(a_odds_ratio, 8) == 2  # with beh_odds_ratios = [2, 3, 4]

        a.beh = [1, 0, 1]
        p = a.suicide_risk(odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev)
        a_odds = p / (1 - p)
        general_odds = gen_sui_prev / (1 - gen_sui_prev)
        a_odds_ratio = a_odds / general_odds
        assert round(a_odds / general_odds, 10) == 8  # with beh_odds_ratios = [2, 3, 4]

        # When accounting for ave_beh == 2
        a.beh = [1, 1, 0]
        p = a.suicide_risk(odds_ratios=[2, 2, 2], gen_sui_prev=gen_sui_prev, ave_beh=2)
        assert round(p, 4) == gen_sui_prev

        # When accounting for ave_beh == 1
        a.beh = [1, 1, 1]
        p = a.suicide_risk(odds_ratios=[2, 2, 2], gen_sui_prev=gen_sui_prev, ave_beh=1)
        a_odds = p / (1 - p)
        general_odds = gen_sui_prev / (1 - gen_sui_prev)
        a_odds_ratio = a_odds / general_odds
        assert round(a_odds_ratio, 8) == 4

    def test_consider_suicide(self):
        a = Agent(id=1, n_beh=3, n_interactions=3, baserates=None)

        assert a.attempts == 0

        gen_sui_prev = 1 / 1000  # very low baserate
        beh_odds_ratios = [1000, 1000, 1000]  # very high risk factors

        # No beh risk factors implies low attempt prob
        a.beh = [0, 0, 0]
        outcome = a.consider_suicide(
            odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev
        )
        assert outcome == 0
        assert a.attempts == 0

        # Attempts should happen when a has many beh risk factors
        a.beh = [1, 1, 1]
        outcome = a.consider_suicide(
            odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev
        )
        assert outcome == 1
        assert a.attempts == 1

        # Test for increment of attempts
        outcome = a.consider_suicide(
            odds_ratios=beh_odds_ratios, gen_sui_prev=gen_sui_prev
        )
        assert outcome == 1
        assert a.attempts == 2
