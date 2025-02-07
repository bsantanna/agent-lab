from typing_extensions import Iterator

from app.domain.models import AgentSetting
from app.domain.repositories.agents import AgentSettingRepository


class AgentSettingService:
    def __init__(self, agent_setting_repository: AgentSettingRepository) -> None:
        self.repository: AgentSettingRepository = agent_setting_repository

    def get_agent_settings(self, agent_id: str) -> Iterator[AgentSetting]:
        return self.repository.get_all(agent_id=agent_id)

    def create_agent_setting(
        self, agent_id: str, setting_key: str, setting_value: str
    ) -> AgentSetting:
        return self.repository.add(
            agent_id=agent_id, setting_key=setting_key, setting_value=setting_value
        )

    def update_by_key(
        self, agent_id: str, setting_key: str, setting_value: str
    ) -> AgentSetting:
        return self.repository.update_by_key(
            agent_id=agent_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )
