from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(
        self,
        adaptive_rag_agent: AgentBase,
        test_echo_agent: AgentBase,
        three_phase_react_agent: AgentBase,
        vision_document_agent: AgentBase,
        react_rag_agent: AgentBase,
    ):
        self.registry = {
            "adaptive_rag": adaptive_rag_agent,
            "react_rag": react_rag_agent,
            "test_echo": test_echo_agent,
            "three_phase_react": three_phase_react_agent,
            "vision_document": vision_document_agent,
        }

    def get_agent(self, agent_type: str) -> AgentBase:
        return self.registry[agent_type]
