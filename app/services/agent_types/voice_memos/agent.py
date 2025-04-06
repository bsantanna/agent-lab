from langgraph.graph import MessagesState
from langgraph.managed import RemainingSteps
from typing_extensions import Annotated, List

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import join_messages, WebAgentBase, AgentUtils


class AgentState(MessagesState):
    agent_id: str
    query: str
    next: str
    collection_name: str
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    researcher_system_prompt: str
    deep_search_mode: bool
    execution_plan: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps


class VoiceMemosAgent(WebAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def get_workflow_builder(self, agent_id: str):
        pass

    def create_default_settings(self, agent_id: str):
        pass

    def get_input_params(self, message_request: MessageRequest) -> dict:
        pass
