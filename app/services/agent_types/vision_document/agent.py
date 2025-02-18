from pathlib import Path

import hvac
from langgraph.graph import add_messages
from typing_extensions import TypedDict, List, Annotated

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import WorkflowAgent
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AgentState(TypedDict):
    agent_id: str
    query: str
    generation: str
    messages: Annotated[List, add_messages]
    image_base64: str
    execution_system_prompt: str


class VisionDocumentAgent(WorkflowAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
        attachment_service: AttachmentService,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
            vault_client=vault_client,
            graph_persistence_factory=graph_persistence_factory,
        )
        self.attachment_service = attachment_service

    def get_workflow_builder(self, agent_id: str):
        pass

    def get_input_params(self, message_request: MessageRequest):
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        return {
            "agent_id": message_request.agent_id,
            "query": message_request.message_content,
            "execution_system_prompt": settings_dict["execution_system_prompt"],
        }

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        execution_prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=execution_prompt,
        )
