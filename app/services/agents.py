from typing import Iterator

from app.domain.exceptions.base import InvalidFieldError
from app.domain.models import Agent
from app.domain.repositories.agents import AgentRepository
from app.domain.repositories.language_models import LanguageModelNotFoundError
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.registry import AgentRegistry
from app.services.language_models import LanguageModelService


class AgentService:
    def __init__(
        self,
        agent_repository: AgentRepository,
        agent_setting_service: AgentSettingService,
        agent_registry: AgentRegistry,
        language_model_service: LanguageModelService,
    ) -> None:
        self.repository: AgentRepository = agent_repository
        self.setting_service: AgentSettingService = agent_setting_service
        self.registry: AgentRegistry = agent_registry
        self.language_model_service: LanguageModelService = language_model_service

    def get_agents(self) -> Iterator[Agent]:
        return self.repository.get_all()

    def get_agent_by_id(self, agent_id: str) -> Agent:
        return self.repository.get_by_id(agent_id)

    def create_agent(
        self,
        agent_name: str,
        agent_type: str,
        language_model_id: str,
    ) -> Agent:
        # verify language model
        try:
            self.language_model_service.get_language_model_by_id(language_model_id)
        except LanguageModelNotFoundError:
            raise InvalidFieldError(
                field_name="language_model_id", reason="language model not found"
            )

        # create agent
        agent = self.repository.add(
            agent_name=agent_name,
            agent_type=agent_type,
            language_model_id=language_model_id,
        )

        # default settings for given agent_type
        self.registry.get_agent(agent_type).create_default_settings(agent_id=agent.id)

        return agent

    def delete_agent_by_id(self, agent_id: str) -> None:
        return self.repository.delete_by_id(agent_id)

    def update_agent(self, agent_id: str, agent_name: str) -> Agent:
        return self.repository.update_agent(agent_id=agent_id, agent_name=agent_name)
