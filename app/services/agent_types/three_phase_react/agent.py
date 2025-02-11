from pathlib import Path

from langgraph.constants import START, END
from langgraph.managed import RemainingSteps
from typing_extensions import TypedDict, List, Annotated

import hvac
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


class AgentState(TypedDict):
    agent_id: str
    query: str
    generation: str
    documents: List[str]
    messages: Annotated[List, add_messages]
    remaining_steps: RemainingSteps
    knowledge_base: str
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
        current_dir = Path(__file__).parent

        preparation_prompt = self.read_file_content(
            f"{current_dir}/default_conclusion_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="preparation_system_prompt",
            setting_value=preparation_prompt,
        )

        execution_prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=execution_prompt,
        )

        conclusion_prompt = self.read_file_content(
            f"{current_dir}/default_conclusion_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="conclusion_system_prompt",
            setting_value=conclusion_prompt,
        )

        knowledge_base = self.read_file_content(
            f"{current_dir}/default_knowledge_base.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="knowledge_base",
            setting_value=knowledge_base,
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)

        # node definitions

        # edge definitions
        workflow_builder.add_edge(START, "preparation_agent")
        workflow_builder.add_edge("preparation_agent", "execution_agent")
        workflow_builder.add_edge("execution_agent", "conclusion_agent")
        workflow_builder.add_edge("conclusion_agent", END)

        return workflow_builder

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
            "knowledge_base": settings_dict["knowledge_base"],
            "preparation_system_prompt": settings_dict["preparation_system_prompt"],
            "execution_system_prompt": settings_dict["execution_system_prompt"],
            "conclusion_system_prompt": settings_dict["conclusion_system_prompt"],
            "messages": [],
        }
