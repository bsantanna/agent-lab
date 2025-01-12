from typing import Iterator
from uuid import uuid4

from app.domain.models import Agent
from app.domain.repositories.agent import AgentRepository


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
