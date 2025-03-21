from pathlib import Path

import hvac

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import AgentBase
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService

from langgraph.prebuilt import create_react_agent


class ReactRagAgent(AgentBase):
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
        )
        self.graph_persistence_factory = graph_persistence_factory
        self.document_repository = document_repository

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent
        prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=prompt,
        )
        collection_name = self.read_file_content(
            f"{current_dir}/default_collection_name.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="collection_name",
            setting_value=collection_name,
        )

    def get_workflow(self, agent_id: str):
        chat_model = self.get_chat_model(agent_id)
        settings = self.agent_setting_service.get_agent_settings(agent_id)
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }
        checkpointer = self.graph_persistence_factory.build_checkpoint_saver()

        return create_react_agent(
            model=chat_model,
            prompt=settings_dict["execution_system_prompt"],
            tools=[],
            checkpointer=checkpointer,
        )

    def get_input_params(self, message_request: MessageRequest) -> dict:
        query = message_request.message_content
        embeddings_model = self.get_embeddings_model(message_request.agent_id)
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }
        collection_name = settings_dict["collection_name"]
        documents = self.document_repository.search(
            embeddings_model=embeddings_model,
            collection_name=collection_name,
            query=query,
            size=7,
        )
        context = "\n---\n".join(document.page_content for document in documents)
        return {
            "messages": [
                ("user", f"<query>{query}</query> <context>{context}</context>")
            ],
        }

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        workflow = self.get_workflow(message_request.agent_id)
        config = {
            "configurable": {
                "thread_id": message_request.agent_id,
            },
            "recursion_limit": 30,
        }
        inputs = self.get_input_params(message_request)
        workflow_result = workflow.invoke(inputs, config)
        return MessageBase(
            message_role="assistant",
            message_content=workflow_result["messages"][-1].content,
            agent_id=message_request.agent_id,
        )
