import hvac

from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import AgentBase
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class TestEchoAgent(AgentBase):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
            vault_client=vault_client,
        )

    def create_default_settings(self, agent_id: str):
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="dummy_setting",
            setting_value="dummy_value",
        )

    def get_input_params(self, message_request: MessageRequest) -> dict:
        return {}

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        return MessageBase(
            message_role="assistant",
            message_content=f"Echo: {message_request.message_content}",
            agent_id=message_request.agent_id,
        )
