from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(
        self,
        adaptive_rag_agent: AgentBase,
        agreement_planner_agent: AgentBase,
        coordinator_planner_supervisor_agent: AgentBase,
        react_rag_agent: AgentBase,
        test_echo_agent: AgentBase,
        vision_document_agent: AgentBase,
        voice_memos_agent: AgentBase,
        azure_entra_id_voice_memos_agent: AgentBase,
    ):
        self.registry = {
            "adaptive_rag": adaptive_rag_agent,
            "agreement_planner": agreement_planner_agent,
            "coordinator_planner_supervisor": coordinator_planner_supervisor_agent,
            "react_rag": react_rag_agent,
            "test_echo": test_echo_agent,
            "vision_document": vision_document_agent,
            "voice_memos": voice_memos_agent,
            "azure_entra_id_voice_memos": azure_entra_id_voice_memos_agent,
        }

    def get_agent(self, agent_type: str) -> AgentBase:
        return self.registry[agent_type]
