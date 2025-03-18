from typing_extensions import TypedDict, List, Annotated

import hvac
from langchain_core.messages import AnyMessage
from langgraph.graph import  add_messages

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.react_rag.agent import ReactRagAgent
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AgentState(TypedDict):
    query: str
    generation: str
    documents: List[str]
    messages: Annotated[List[AnyMessage], add_messages]
    preparation_system_prompt: str
    execution_system_prompt: str
    conclusion_system_prompt: str


class ThreePhaseReactAgent(ReactRagAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
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
            document_repository=document_repository,
        )

    def create_default_settings(self, agent_id: str):
        # TODO
        pass

    def get_workflow_builder(self, agent_id: str):
        # TODO
        pass
