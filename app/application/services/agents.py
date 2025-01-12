from typing import Iterator
from uuid import uuid4

from app.domain.models import Agent, AgentSetting
from app.domain.repositories.agents import AgentRepository, AgentSettingRepository


class AgentService:
    def __init__(self, agent_repository: AgentRepository) -> None:
        self._repository: AgentRepository = agent_repository

    def get_agents(self) -> Iterator[Agent]:
        return self._repository.get_all()

    def get_agent_by_id(self, agent_id: int) -> Agent:
        return self._repository.get_by_id(agent_id)

    def create_agent(self) -> Agent:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_agent_by_id(self, agent_id: int) -> None:
        return self._repository.delete_by_id(agent_id)


class AgentSettingService:
    def __init__(self, agent_setting_repository: AgentSettingRepository) -> None:
        self._repository: AgentSettingRepository = agent_setting_repository

    def get_agent_settings(self) -> Iterator[AgentSetting]:
        return self._repository.get_all()

    def get_agent_setting_by_id(self, agent_setting_id: int) -> AgentSetting:
        return self._repository.get_by_id(agent_setting_id)

    def create_agent_setting(self) -> AgentSetting:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_agent_setting_by_id(self, agent_setting_id: int) -> None:
        return self._repository.delete_by_id(agent_setting_id)
