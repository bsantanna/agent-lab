from pathlib import Path
from typing import TypedDict, List, Annotated

import hvac
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, add_messages

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.adaptive_rag.agent import AdaptiveRagAgent
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService
from app.services.messages import MessageService


class AgentState(TypedDict):
    query: str
    generation: str
    documents: List[str]
    messages: Annotated[List[AnyMessage], add_messages]
    preparation_system_prompt: str
    execution_system_prompt: str
    conclusion_system_prompt: str


class ThreePhaseReactAgent(AdaptiveRagAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
        message_service: MessageService,
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
            message_service=message_service,
            document_repository=document_repository,
        )

    def create_default_settings(self, agent_id: str):
        super().create_default_settings(agent_id)

        current_dir = Path(__file__).parent
        conclusion_prompt = self.read_file_content(
            f"{current_dir}/default_conclusion_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="conclusion_system_prompt",
            setting_value=conclusion_prompt,
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)

        return workflow_builder

    def get_input_params(self, message_request: MessageRequest):
        pass
