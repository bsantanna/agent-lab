from pathlib import Path
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages, StateGraph

from typing import Annotated, List, TypedDict

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import WorkflowAgent
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


class AdaptiveRagAgent(WorkflowAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        graph_persistence_factory: GraphPersistenceFactory,
        document_repository: DocumentRepository,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
            graph_persistence_factory=graph_persistence_factory,
        )
        self.document_repository = document_repository

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        preparation_prompt = self.read_file_content(
            f"{current_dir}/default_preparation_system_prompt.txt"
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

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        # chat_model = self.get_chat_model(agent_id)

        return workflow_builder

    # def retrieve(self, state):
    #     """
    #     Retrieve documents

    #     Args:
    #         state (dict): The current graph state

    #     Returns:
    #         state (dict): New key added to state, documents, that contains retrieved documents
    #     """
    #     question = state["question"]
    #     assistant_name = state["assistant_name"]
    #     instructions = state["instructions"]
    #     domain = state["domain"]
    #     hits = vector_store_builder.build(assistant_name).search(
    #         question,
    #         search_type="similarity",
    #     )
    #     return {
    #         "documents": hits,  # [doc.page_content for doc in hits],
    #         "question": question,
    #         "assistant_name": assistant_name,
    #         "instructions": instructions,
    #         "domain": domain,
    #     }

    def get_input_params(self, message_request: MessageRequest):
        return {}
