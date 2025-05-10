from typing_extensions import Literal

from langgraph.graph import MessagesState
from langgraph.types import Command

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import SupervisedWorkflowAgentBase, AgentUtils


class AgreementPlanner(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def get_coordinator(
        self, state: MessagesState
    ) -> Command[Literal["planner", "__end__"]]:
        pass

    def get_planner(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        pass

    def get_supervisor(self, state: MessagesState) -> Command:
        pass

    def get_reporter(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        pass

    def get_workflow_builder(self, agent_id: str):
        pass

    def create_default_settings(self, agent_id: str):
        pass

    def get_input_params(self, message_request: MessageRequest) -> dict:
        pass
