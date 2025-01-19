import os
from abc import ABC, abstractmethod

from app.domain.exceptions.base import ResourceNotFoundError
from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService


class AgentBase(ABC):
    def __init__(self, agent_setting_service: AgentSettingService):
        self.setting_service = agent_setting_service

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
        agent_setting_service: AgentSettingService,
        graph_persistence_factory: GraphPersistenceFactory,
    ):
        super().__init__(agent_setting_service)
        self.graph_persistence_factory = graph_persistence_factory

    @abstractmethod
    def get_workflow_builder(self):
        pass

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        checkpointer = self.graph_persistence_factory.build_checkpoint_saver()
        self.get_workflow_builder().compile(checkpointer=checkpointer)
        return None
