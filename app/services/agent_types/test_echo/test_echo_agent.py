import json

from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_types.base import AgentBase, AgentUtils


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
        return json.dumps(message_request.to_dict())

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        return MessageBase(
            message_role="assistant",
            message_content=self.format_response(
                MessagesState(
                    messages=[
                        AIMessage(content=f"Echo: {message_request.message_content}")
                    ]
                )
            ),
            agent_id=message_request.agent_id,
        )
