from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import AgentBase


class TestEchoAgent(AgentBase):
    def __init__(self, agent_setting_service: AgentSettingService):
        super().__init__(agent_setting_service)

    def create_default_settings(self, agent_id: str):
        self.setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="dummy_setting",
            setting_value="dummy_value",
        )

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        return MessageBase(
            message_role="assistant",
            message_content=f"Echo: {message_request.message_content}",
            agent_id=message_request.agent_id,
        )
