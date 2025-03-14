import os
from abc import ABC, abstractmethod

import hvac
from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from typing_extensions import List

from app.domain.exceptions.base import ResourceNotFoundError
from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


def join_messages(left: List, right: List) -> List:
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]

    return left + right


class AgentBase(ABC):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
    ):
        self.agent_service = agent_service
        self.agent_setting_service = agent_setting_service
        self.language_model_service = language_model_service
        self.language_model_setting_service = language_model_setting_service
        self.integration_service = integration_service
        self.vault_client = vault_client

    @abstractmethod
    def create_default_settings(self, agent_id: str):
        pass

    @abstractmethod
    def process_message(self, message_request: MessageRequest) -> MessageBase:
        pass

    def get_embeddings_model(self, agent_id) -> Embeddings:
        agent = self.agent_service.get_agent_by_id(agent_id)
        language_model = self.language_model_service.get_language_model_by_id(
            agent.language_model_id
        )
        integration = self.integration_service.get_integration_by_id(
            language_model.integration_id
        )
        secrets = self.vault_client.secrets.kv.read_secret_version(
            path=f"integration_{integration.id}", raise_on_deleted_version=False
        )
        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        lm_settings = self.language_model_setting_service.get_language_model_settings(
            agent.language_model_id
        )

        lm_settings_dict = {
            setting.setting_key: setting.setting_value for setting in lm_settings
        }

        if integration.integration_type == "openai_api_v1":
            return OpenAIEmbeddings(
                model=lm_settings_dict["embeddings"],
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        # not available
        # elif integration.integration_type == "xai_api_v1":
        #    return OpenAIEmbeddings(
        #       model=lm_settings_dict["embeddings"],
        #       base_url=api_endpoint,
        #       api_key=api_key
        #    )
        elif integration.integration_type == "ollama_api_v1":
            return OllamaEmbeddings(
                model=lm_settings_dict["embeddings"], base_url=api_endpoint
            )
        else:
            return OllamaEmbeddings(
                model=lm_settings_dict["embeddings"],
                base_url=f"{os.getenv('OLLAMA_ENDPOINT')}",
            )

    def get_chat_model(self, agent_id) -> BaseChatModel:
        agent = self.agent_service.get_agent_by_id(agent_id)
        language_model = self.language_model_service.get_language_model_by_id(
            agent.language_model_id
        )
        lm_settings = self.language_model_setting_service.get_language_model_settings(
            agent.language_model_id
        )
        lm_settings_dict = {
            setting.setting_key: setting.setting_value for setting in lm_settings
        }
        integration = self.integration_service.get_integration_by_id(
            language_model.integration_id
        )
        secrets = self.vault_client.secrets.kv.read_secret_version(
            raise_on_deleted_version=False, path=f"integration_{integration.id}"
        )
        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        if (
            integration.integration_type == "openai_api_v1"
            or integration.integration_type == "xai_api_v1"
        ):
            return ChatOpenAI(
                model_name=language_model.language_model_tag,
                temperature=float(lm_settings_dict["temperature"]),
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        elif integration.integration_type == "anthropic_api_v1":
            return ChatAnthropic(
                model=language_model.language_model_tag,
                temperature=float(lm_settings_dict["temperature"]),
                anthropic_api_url=api_endpoint,
                anthropic_api_key=api_key,
            )
        else:
            return ChatOllama(
                model=language_model.language_model_tag,
                temperature=float(lm_settings_dict["temperature"]),
                base_url=api_endpoint,
            )

    def read_file_content(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(file_path)

        with open(file_path, "r") as file:
            return file.read().strip()


class WorkflowAgent(AgentBase, ABC):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
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

    @abstractmethod
    def get_workflow_builder(self, agent_id: str):
        pass

    @abstractmethod
    def get_input_params(self, message_request: MessageRequest):
        pass

    def create_thought_chain(
        self,
        human_input: str,
        ai_response: str,
        connection: str = None,
        llm: BaseChatModel = None,
        token_limit: int = 1024,
    ):
        # Build the chain of thought
        prompt = (
            f"Summarize the text delimited by <ai_resp></ai_resp> using at most {token_limit} tokens.\n"
            f"<ai_resp>{ai_response}</ai_resp>"
        )
        processed_response = (
            llm.invoke(prompt).content if llm is not None else ai_response
        )
        thought_chain = (
            f"First: The human asked or stated - {human_input}\n"
            f"Then: The AI responded with - {processed_response}\n"
            f"Connection: {connection}"
            if connection is not None
            else ""
        )

        return thought_chain

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        checkpointer = self.graph_persistence_factory.build_checkpoint_saver()
        workflow = self.get_workflow_builder(message_request.agent_id).compile(
            checkpointer=checkpointer
        )
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
            message_content=workflow_result["generation"],
            agent_id=message_request.agent_id,
        )
