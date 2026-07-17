from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from agent_lab import AgentBase, AgentUtils, discoverable_agent
from agent_lab.interface.api.messages.schema import Message, MessageRequest
from agent_lab.services.tasks import TaskProgress


@discoverable_agent("{{ cookiecutter.package_name }}_echo")
class EchoAgent(AgentBase):
    """Minimal agent: echoes the incoming message without calling an LLM."""

    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def create_default_settings(self, agent_id: str, schema: str):
        pass

    def get_input_params(self, message_request: MessageRequest, schema: str) -> dict:
        return message_request.model_dump()

    def process_message(self, message_request: MessageRequest, schema: str) -> Message:
        message_content, response_data = self.format_response(
            MessagesState(
                messages=[AIMessage(content=f"Echo: {message_request.message_content}")]
            )
        )

        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=message_request.agent_id,
                status="completed",
                message_content=message_content,
                response_data=response_data,
            )
        )

        return Message(
            message_role="assistant",
            message_content=message_content,
            response_data=response_data,
            agent_id=message_request.agent_id,
        )
