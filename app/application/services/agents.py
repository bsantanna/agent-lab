import os
from pathlib import Path
from typing import Iterator

from app.application.services.language_models import LanguageModelService
from app.domain.exceptions.base import InvalidFieldError, ResourceNotFoundError
from app.domain.models import Agent, AgentSetting
from app.domain.repositories.agents import AgentRepository, AgentSettingRepository
from app.domain.repositories.language_models import LanguageModelNotFoundError


class AgentSettingService:
    def __init__(self, agent_setting_repository: AgentSettingRepository) -> None:
        self._repository: AgentSettingRepository = agent_setting_repository

    def get_agent_settings(self, agent_id: str) -> Iterator[AgentSetting]:
        return self._repository.get_all(agent_id=agent_id)

    def create_agent_setting(
        self, agent_id: str, setting_key: str, setting_value: str
    ) -> AgentSetting:
        return self._repository.add(
            agent_id=agent_id, setting_key=setting_key, setting_value=setting_value
        )

    def update_by_key(
        self, agent_id: str, setting_key: str, setting_value: str
    ) -> AgentSetting:
        return self._repository.update_by_key(
            agent_id=agent_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )


class AgentService:
    def __init__(
        self,
        agent_repository: AgentRepository,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
    ) -> None:
        self._repository: AgentRepository = agent_repository
        self._setting_service: AgentSettingService = agent_setting_service
        self._language_model_service: LanguageModelService = language_model_service

    def get_agents(self) -> Iterator[Agent]:
        return self._repository.get_all()

    def get_agent_by_id(self, agent_id: str) -> Agent:
        return self._repository.get_by_id(agent_id)

    def create_agent(
        self, agent_name: str, agent_type: str, language_model_id: str
    ) -> Agent:
        # verify language model
        try:
            self._language_model_service.get_language_model_by_id(language_model_id)
        except LanguageModelNotFoundError:
            raise InvalidFieldError(
                field_name="language_model_id", reason="language model not found"
            )

        # create agent
        agent = self._repository.add(
            agent_name=agent_name,
            agent_type=agent_type,
            language_model_id=language_model_id,
        )

        # default settings per agent_type
        self._create_default_settings_for_agent_type(
            agent_id=agent.id, agent_type=agent_type
        )

        return agent

    def delete_agent_by_id(self, agent_id: str) -> None:
        return self._repository.delete_by_id(agent_id)

    def update_agent(self, agent_id: str, agent_name: str) -> Agent:
        return self._repository.update_agent(agent_id=agent_id, agent_name=agent_name)

    def _create_default_settings_for_agent_type(self, agent_id: str, agent_type: str):
        current_dir = Path(__file__).parent

        if agent_type == "three_phase_react":
            preparation_prompt = self._read_file_content(
                f"{current_dir}/agent_types/{agent_type}/default_preparation_system_prompt.txt"
            )
            self._setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key="preparation_prompt",
                setting_value=preparation_prompt,
            )

            execution_prompt = self._read_file_content(
                f"{current_dir}/agent_types/{agent_type}/default_execution_system_prompt.txt"
            )
            self._setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key="execution_prompt",
                setting_value=execution_prompt,
            )

            conclusion_prompt = self._read_file_content(
                f"{current_dir}/agent_types/{agent_type}/default_conclusion_system_prompt.txt"
            )
            self._setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key="conclusion_prompt",
                setting_value=conclusion_prompt,
            )

    def _read_file_content(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(file_path)

        with open(file_path, "r") as file:
            return file.read().strip()
