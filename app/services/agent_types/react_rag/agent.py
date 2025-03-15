from pathlib import Path
from typing_extensions import TypedDict, List, Annotated

import hvac
from langgraph.graph import StateGraph

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import join_messages
from app.services.agent_types.vision_document.agent import VisionDocumentAgent
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AgentState(TypedDict):
    agent_id: str
    query: str
    generation: dict
    documents: List[str]
    messages: Annotated[List, join_messages]
    image_base64: str
    image_content_type: str
    execution_system_prompt: str


class ReactRagAgent(VisionDocumentAgent):
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
        document_repository: DocumentRepository,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
            vault_client=vault_client,
            graph_persistence_factory=graph_persistence_factory,
            attachment_service=attachment_service,
        )
        self.document_repository = (document_repository,)

    def create_default_settings(self, agent_id: str):
        super().create_default_settings(agent_id)

        current_dir = Path(__file__).parent
        prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=prompt,
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        # TODO
        return workflow_builder

    def get_input_params(self, message_request: MessageRequest):
        if message_request.attachment_id is not None:
            input_params = super().get_input_params(message_request)
        else:
            settings = self.agent_setting_service.get_agent_settings(
                message_request.agent_id
            )
            settings_dict = {
                setting.setting_key: setting.setting_value for setting in settings
            }
            input_params = {
                "agent_id": message_request.agent_id,
                "query": message_request.message_content,
                "execution_system_prompt": settings_dict["execution_system_prompt"],
            }

        return input_params
