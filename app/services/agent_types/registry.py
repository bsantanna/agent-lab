from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(self, tp_react_agent: AgentBase):
        self._registry = {"three_phase_react": tp_react_agent}

    def get_agent(self, agent_type: str):
        return self._registry[agent_type]
