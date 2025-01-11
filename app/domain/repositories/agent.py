from contextlib import AbstractContextManager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent


class AgentRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[Agent]:
        with self.session_factory() as session:
            return session.query(Agent).all()

    def get_by_id(self, agent_id: int) -> Agent:
        with self.session_factory() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise AgentNotFoundError(agent_id)
            return agent

    def add(self, email: str, password: str, is_active: bool = True) -> Agent:
        with self.session_factory() as session:
            agent = Agent(email=email, hashed_password=password, is_active=is_active)
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def delete_by_id(self, agent_id: int) -> None:
        with self.session_factory() as session:
            entity: Agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if not entity:
                raise AgentNotFoundError(agent_id)
            session.delete(entity)
            session.commit()


class AgentNotFoundError(NotFoundError):
    entity_name: str = "Agent"
