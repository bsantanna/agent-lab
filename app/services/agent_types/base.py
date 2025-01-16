import os
from abc import ABC, abstractmethod

from app.domain.exceptions.base import ResourceNotFoundError
from app.interface.api.messages.schema import MessageRequest, MessageResponse
from app.services.agent_settings import AgentSettingService


class AgentBase(ABC):
    def __init__(self, agent_setting_service: AgentSettingService):
        self.setting_service = agent_setting_service

    @abstractmethod
    def create_default_settings(self, agent_id: str):
        pass

    @abstractmethod
    def process_message(self, message_request: MessageRequest) -> MessageResponse:
        pass

    def read_file_content(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(file_path)

        with open(file_path, "r") as file:
            return file.read().strip()
