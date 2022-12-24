import random


class Intervention:
    def __init__(
        self,
        intv_class_name,
        start_tick,
        duration,
        tar_severity,
        p_rewire,
        p_enrolled,
        p_beh_change,
    ) -> None:
        self.intv_class_name = intv_class_name
        self.start_tick = start_tick
        self.duration = duration
        self.last_tick = start_tick + duration - 1
        self.tar_severity = tar_severity
        self.p_rewire = p_rewire
        self.p_enrolled = p_enrolled
        self.p_beh_change = p_beh_change
        self.beh_changed = 0

    def is_setup_phase(self, t):
        return t == self.start_tick

    def is_active_phase(self, t):
        return (self.start_tick <= t) and (t <= self.last_tick)

    def setup(self, agents, network, sui_ORs, **kwargs):
        self.__dict__.update(kwargs)
        self.sui_ORs = sui_ORs
        self.enrolled_names = [a.name for a in agents]

    def intervene(self, agents, network):
        pass

    def risk_factor_ranks(self, sui_ORs):
        enumerated_risks = list(enumerate(sui_ORs))
        ranked_risks = sorted(enumerated_risks, key=lambda pair: pair[1])
        ranks = [pair[0] for pair in ranked_risks]

        return ranks

    def target_behaviors(self, sui_ORs, tar_severity):
        ranked_risks = self.risk_factor_ranks(sui_ORs)
        tar_ranks = [round(p * len(ranked_risks)) for p in tar_severity]
        tar_beh = ranked_risks[tar_ranks[0] : tar_ranks[1]]

        return tar_beh

    def enrolled_agents(self, agents):
        assert self.enrolled_names

        return [a for a in agents if a.name in self.enrolled_names]

    def as_dict(self):
        d = {
            "intv_type": self.__class__.__name__,
            "start_tick": self.start_tick,
            "duration": self.duration,
            "last_tick": self.last_tick,
            "beh_changed": self.beh_changed,
        }

        return d


class NetworkIntervention(Intervention):
    def setup(self, agents, network, **kwargs):
        super().setup(agents, network, **kwargs)
        self.tar_beh = self.target_behaviors(self.sui_ORs, self.tar_severity)

        self.enrolled_names = []
        for agent in agents:
            if random.random() < self.p_enrolled:
                self.enrolled_names.append(agent.name)

                for agent in self.enrolled_agents(agents):
                    agent.enrolled = True

    def intervene(self, agents, network):
        network.rewire_edges(self.p_rewire)

        enrollees = self.enrolled_agents(agents)

        for agent in enrollees:
            for i in self.tar_beh:
                if random.random() < self.p_beh_change:

                    # if this behavior was actually bad to start,
                    # document the improvement
                    self.beh_changed += int(agent.beh[i] == 1)

                    # change behavior for the better
                    agent.beh[i] = 0


class IndividualIntervention(Intervention):
    def prioritize_agents(self, agents, sui_ORs, desc=True):
        risk_scores = []
        for agent in agents:
            risk_score = sum([beh * risk for risk, beh in zip(sui_ORs, agent.beh)])
            risk_scores.append(risk_score)

        sorted_pairs = sorted(zip(risk_scores, agents), key=lambda pair: pair[0])
        ranked_agents = [agent for _, agent in sorted_pairs]

        if desc:
            ranked_agents = list(reversed(ranked_agents))

        return ranked_agents

    def treatable_behaviors(self, sui_ORs, tar_severity):
        tar_ranks = [round(p * len(sui_ORs)) for p in tar_severity]
        self.treatable_beh = tar_ranks[1] - tar_ranks[0]

        return self.treatable_beh

    def setup(self, agents, network, **kwargs):
        super().setup(agents, network, **kwargs)

        self.treatable_beh = self.treatable_behaviors(self.sui_ORs, self.tar_severity)

        # Enroll the highest risk agents
        ranked_agents = self.prioritize_agents(agents, self.sui_ORs)
        enrolled_agents = ranked_agents[0 : round(self.p_enrolled * len(ranked_agents))]
        enrolled_names = [a.name for a in enrolled_agents]

        self.enrolled_names = enrolled_names

        for agent in self.enrolled_agents(agents):
            agent.enrolled = True

    def priority_behaviors(self, agent):
        risk_ranks = self.risk_factor_ranks(self.sui_ORs)
        active_risks = [i for i in risk_ranks if agent.beh[i] == 1]
        priority_beh = list(reversed(active_risks))

        return priority_beh

    def intervene(self, agents, network):
        enrollees = self.enrolled_agents(agents)

        for agent in enrollees:
            priority_beh = self.priority_behaviors(agent)
            treatable_beh = priority_beh[0 : self.treatable_beh]

            for i in treatable_beh:
                if random.random() < self.p_beh_change:

                    # if this behavior was actually bad to start,
                    # document the improvement
                    self.beh_changed += int(agent.beh[i] == 1)

                    # change the behavior to the better
                    agent.beh[i] = 0


class MockInterventionA(Intervention):
    def setup(self, agents, network, **kwargs):
        super().setup(agents, network, **kwargs)
        self.tar_beh = self.target_behaviors(self.sui_ORs, self.tar_severity)

        self.enrolled_names = []
        for agent in agents:
            if random.random() < self.p_enrolled:
                self.enrolled_names.append(agent.name)

                for agent in self.enrolled_agents(agents):
                    agent.enrolled = True

    def intervene(self, agents, network):

        # Each enrollee has a chance for their total beh to become proportional
        # to their degree. Fewer alters means GREATER total beh
        enrollees = self.enrolled_agents(agents)

        for agent in enrollees:
            old_total = sum(agent.beh)

            if random.random() < self.p_beh_change:
                agent.beh = ([1] * 2) + ([0] * (len(agent.beh) - 2))

                random.shuffle(agent.beh)

                self.beh_changed += old_total - sum(agent.beh)


class MockInterventionB(Intervention):
    def setup(self, agents, network, **kwargs):
        super().setup(agents, network, **kwargs)
        self.tar_beh = self.target_behaviors(self.sui_ORs, self.tar_severity)

        self.enrolled_names = []
        for agent in agents:
            if random.random() < self.p_enrolled:
                self.enrolled_names.append(agent.name)

                for agent in self.enrolled_agents(agents):
                    agent.enrolled = True

    def intervene(self, agents, network):

        # Each enrollee has a chance for their total beh to become proportional
        # to their degree. Fewer alters means GREATER total beh
        enrollees = self.enrolled_agents(agents)

        for agent in enrollees:
            old_total = sum(agent.beh)

            if random.random() < self.p_beh_change:
                agent.beh = ([1] * 2) + ([0] * (len(agent.beh) - 2))

                random.shuffle(agent.beh)

                self.beh_changed += old_total - sum(agent.beh)

        # ALSO There is a random chance edges will simply be deleted
        for e in network.es:
            if random.random() < self.p_rewire:
                network.delete_edges(e.index)
