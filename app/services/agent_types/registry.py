from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(self, test_echo_agent: AgentBase, three_phase_react_agent: AgentBase):
        self._registry = {
            "test_echo": test_echo_agent,
            "three_phase_react": three_phase_react_agent,
        }

    def get_agent(self, agent_type: str) -> AgentBase:
        return self._registry[agent_type]
