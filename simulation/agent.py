from math import exp, log
import random
from statistics import mean


class Agent(object):
    def __init__(self, id, n_beh, max_alters, baserates=None) -> None:
        assert (baserates is None) or (len(baserates) == n_beh)
        assert (baserates is None) or all([(0 <= b) and (b <= 1) for b in baserates])

        self.id = id
        self.name = f"id_{id}"
        self.max_alters = max_alters
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
            "max_alters": self.max_alters,
            "beh": self.beh,
            "atttempt_count": self.attempts,
        }

        return d

    def emulate(self, alter, p):
        assert len(self.beh) == len(alter.beh)

        for i, alter_beh in enumerate(alter.beh):
            if random.random() < p:
                self.beh[i] = alter_beh

    def emulate_alters(self, agents, network, p):
        alters = self.alters(agents, network)
        for alter in alters:
            self.emulate(alter, p)

    def spontaneously_change(self, baserates, susceptibility):
        assert len(baserates) == len(self.beh)
        assert (0 <= susceptibility) and (susceptibility <= 1)

        for i, beh in enumerate(self.beh):
            beh_is_susceptible = random.random() < susceptibility
            if beh_is_susceptible:
                self.beh[i] = int(random.random() < baserates[i])

        return self

    def similarity(self, alter):
        sim = mean([self.beh[i] == alter.beh[i] for i, b in enumerate(self.beh)])

        assert (0 <= sim) and (sim <= 1)

        return sim

    def recruit_alters(self, agents, network, sim_thresh=0.50):
        assert (0 <= sim_thresh) and (sim_thresh <= 1)

        neighborhood = network.neighborhood(self.network_index(network))
        pot_alters = [a for a in agents if a.network_index(network) not in neighborhood]

        for alter in pot_alters:
            both_available = self.available(network) and alter.available(network)
            similar_enough = self.similarity(alter) >= sim_thresh
            if both_available and similar_enough:
                new_edge = (self.network_index(network), alter.network_index(network))
                network.add_edges([new_edge])

        return self

    def prune_alters(self, agents, network, sim_thresh=0.50):
        assert (0 <= sim_thresh) and (sim_thresh <= 1)

        alters = self.alters(agents, network)

        for alter in alters:
            if self.similarity(alter) < sim_thresh:
                bad_edge = (self.network_index(network), alter.network_index(network))
                network.delete_edges([bad_edge])

        return self

    def available(self, network):
        neighbor_indices = network.neighborhood(self.network_index(network))
        has_open_slots = len(neighbor_indices) < self.max_alters

        return has_open_slots

    def network_index(self, network):
        return network.vs["name"].index(self.name)

    def alters(self, agents, network):
        cur_agent_index = self.network_index(network)
        alter_indices = network.neighbors(cur_agent_index)
        alters = [a for a in agents if a.network_index(network) in alter_indices]

        return alters

    def suicide_risk(self, odds_ratios, gen_sui_prev):
        assert len(odds_ratios) == len(self.beh)

        intercept = log(gen_sui_prev / (1 - gen_sui_prev))
        b = [log(odds_ratio) for odds_ratio in odds_ratios]
        log_odds = sum([b_i * beh_i for b_i, beh_i in zip(b, self.beh)])
        p = 1 / (1 + exp(-(intercept + log_odds)))

        self.current_risk = p

        return p

    def consider_suicide(self, odds_ratios, gen_sui_prev):

        cur_risk = self.suicide_risk(odds_ratios, gen_sui_prev)
        attempt_yn = int(random.random() < cur_risk)

        if attempt_yn:
            self.attempts = self.attempts + 1

        return attempt_yn
