from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from app.interface.api.messages.schema import MessageRequest, Message
from app.services.agent_types.base import AgentBase, AgentUtils
from app.services.tasks import TaskProgress


class TestEchoAgent(AgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def create_default_settings(self, agent_id: str):
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="dummy_setting",
            setting_value="dummy_value",
        )

    def get_input_params(self, message_request: MessageRequest) -> dict:
        return message_request.to_dict()

    def process_message(self, message_request: MessageRequest) -> Message:
        message_content, response_data = self.format_response(
            MessagesState(
                messages=[AIMessage(content=f"Echo: {message_request.message_content}")]
            )
        )

        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=message_request.agent_id,
                status="in_progress",
                message_content=f"echo: {message_request.message_content}",
            )
        )

        return Message(
            message_role="assistant",
            message_content=message_content,
            response_data=response_data,
            agent_id=message_request.agent_id,
        )
