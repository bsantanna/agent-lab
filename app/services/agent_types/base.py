import os
from abc import ABC, abstractmethod

from app.domain.exceptions.base import ResourceNotFoundError
from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AgentBase(ABC):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
    ):
        self.agent_service = agent_service
        self.agent_setting_service = agent_setting_service
        self.language_model_service = language_model_service
        self.language_model_setting_service = language_model_setting_service
        self.integration_service = integration_service

    @abstractmethod
    def create_default_settings(self, agent_id: str):
        pass

    @abstractmethod
    def process_message(self, message_request: MessageRequest) -> MessageBase:
        pass

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
        graph_persistence_factory: GraphPersistenceFactory,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
        )
        self.graph_persistence_factory = graph_persistence_factory

    @abstractmethod
    def get_workflow_builder(self, agent_id: str):
        pass

    @abstractmethod
    def get_input_params(self, message_request: MessageRequest):
        pass

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        checkpointer = self.graph_persistence_factory.build_checkpoint_saver()
        workflow = self.get_workflow_builder(message_request.agent_id).compile(
            checkpointer=checkpointer
        )
        config = {"configurable": {"thread_id": message_request.agent_id}}
        inputs = self.get_input_params(message_request)
        workflow_result = workflow.invoke(inputs, config)
        return MessageBase(
            message_role="assistant",
            message_content=workflow_result["generation"],
            agent_id=message_request.agent_id,
        )
