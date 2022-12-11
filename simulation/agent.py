import itertools
from math import exp, log
import random
from statistics import mean


class Agent(object):
    def __init__(self, id, n_beh, n_interactions, baserates=None) -> None:
        assert (baserates is None) or (len(baserates) == n_beh)
        assert (baserates is None) or all([(0 <= b) and (b <= 1) for b in baserates])

        self.id = id
        self.name = f"id_{id}"
        self.n_interactions = n_interactions
        self.current_risk = None
        self.attempts = 0

        if baserates is not None:
            self.beh = [int(random.random() < p) for p in baserates]
        else:
            self.beh = [int(random.random() < 0.50) for _ in range(n_beh)]

    def __str__(self) -> str:
        return f"{self.name}: {'-'.join([str(b) for b in self.beh])}"

    def as_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "n_interactions": self.n_interactions,
            "beh": self.beh,
            "attempt_count": self.attempts,
        }

        return d

    def emulate(self, alter, p):
        for i, alter_beh in enumerate(alter.beh):
            if random.random() < p:
                self.beh[i] = alter_beh

    def emulate_alters_old(self, agents, network, p):
        alters = self.alters(agents, network)

        if any(alters):

            # when n_interactions > len(alters) this intentionally creates repeats
            alter_interactions = random.choices(alters, k=self.n_interactions)

            for alter in alter_interactions:
                self.emulate(alter, p)

    def emulate_alters(self, agents, network, p):
        alters = self.alters(agents, network)

        if not any(alters):
            return None

        for i, beh in enumerate(self.beh):
            if random.random() < p:
                alter = random.choice(alters)
                self.beh[i] = alter.beh[i]

    def spontaneously_change(self, baserates, susceptibility):
        for i, beh in enumerate(self.beh):
            if random.random() < susceptibility:
                self.beh[i] = int(random.random() < baserates[i])

        return self

    def similarity(self, alter):
        sim = mean([self.beh[i] == alter.beh[i] for i, b in enumerate(self.beh)])

        return sim

    def recruit_alters(self, agents, network, sim_thresh=0.50):

        neighborhood = network.neighborhood(self.network_index(network))
        pot_alters = [a for a in agents if a.network_index(network) not in neighborhood]

        for alter in pot_alters:
            similar_enough = self.similarity(alter) >= sim_thresh
            if similar_enough:
                new_edge = (self.network_index(network), alter.network_index(network))
                network.add_edges([new_edge])

        return self

    def prune_alters(self, agents, network, sim_thresh=0.50):

        alters = self.alters(agents, network)

        for alter in alters:
            if self.similarity(alter) < sim_thresh:
                bad_edge = (self.network_index(network), alter.network_index(network))
                network.delete_edges([bad_edge])

        return self

    def network_index(self, network):
        return network.vs["name"].index(self.name)

    def alters(self, agents, network):
        cur_agent_index = self.network_index(network)
        alter_indices = network.neighbors(cur_agent_index)
        alters = [a for a in agents if a.network_index(network) in alter_indices]

        return alters

    def suicide_risk(self, odds_ratios, gen_sui_prev, gen_ave_beh):

        intercept = log(gen_sui_prev / (1 - gen_sui_prev))
        b = [log(odds_ratio) for odds_ratio in odds_ratios]
        log_odds = sum([b_i * beh_i for b_i, beh_i in zip(b, self.beh)])

        # Adjustment so that an agent with sum(beh) == ave_beh will also have
        # A suicide risk equal to gen_sui_prev. This allows from some agents to
        # be healthier than the average person from the general population.
        log_odds_adjustment = mean(b) * gen_ave_beh

        p = 1 / (1 + exp(-(intercept + log_odds - log_odds_adjustment)))

        self.current_risk = p

        return p

    def consider_suicide(self, odds_ratios, gen_sui_prev, gen_ave_beh):

        cur_risk = self.suicide_risk(odds_ratios, gen_sui_prev, gen_ave_beh)
        attempt_yn = int(random.random() < cur_risk)

        if attempt_yn:
            self.attempts = self.attempts + 1

        return attempt_yn
