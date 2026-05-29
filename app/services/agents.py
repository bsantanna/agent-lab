from typing_extensions import Iterator, Optional

from app.domain.models import Agent
from app.domain.repositories.agents import AgentRepository
from app.services.agent_settings import AgentSettingService
from app.services.language_models import LanguageModelService


class AgentService:
    def __init__(
        self,
        agent_repository: AgentRepository,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
    ) -> None:
        self.agent_repository: AgentRepository = agent_repository
        self.agent_setting_service: AgentSettingService = agent_setting_service
        self.language_model_service: LanguageModelService = language_model_service

    def get_agents(self, schema: str) -> Iterator[Agent]:
        return self.agent_repository.get_all(schema)

    def get_agent_by_id(self, agent_id: str, schema: str) -> Agent:
        return self.agent_repository.get_by_id(agent_id, schema)

    def create_agent(
        self,
        agent_name: str,
        agent_type: str,
        schema: str,
        language_model_id: Optional[str] = None,
    ) -> Agent:
        resolved_language_model_id = self._resolve_language_model_id(
            language_model_id, schema
        )
        agent = self.agent_repository.add(
            agent_name=agent_name,
            agent_type=agent_type,
            language_model_id=resolved_language_model_id,
            schema=schema,
        )

        return agent

    def delete_agent_by_id(self, agent_id: str, schema: str) -> None:
        return self.agent_repository.delete_by_id(agent_id, schema)

    def update_agent(
        self,
        agent_id: str,
        agent_name: str,
        schema: str,
        agent_summary: str = None,
        language_model_id: Optional[str] = None,
    ) -> Agent:
        resolved_language_model_id = self._resolve_language_model_id(
            language_model_id, schema
        )
        return self.agent_repository.update_agent(
            agent_id=agent_id,
            agent_name=agent_name,
            language_model_id=resolved_language_model_id,
            agent_summary=agent_summary,
            schema=schema,
        )

    def _resolve_language_model_id(
        self, language_model_id: Optional[str], schema: str
    ) -> Optional[str]:
        if language_model_id is None:
            return None
        language_model = self.language_model_service.get_language_model_by_id(
            language_model_id, schema
        )
        return language_model.id
