from contextlib import AbstractContextManager
from datetime import datetime
from typing import Callable, Iterator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Agent, AgentSetting


class AgentRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[Agent]:
        with self.session_factory() as session:
            return session.query(Agent).filter(Agent.is_active).all()

    def get_by_id(self, agent_id: str) -> Agent:
        with self.session_factory() as session:
            agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not agent:
                raise AgentNotFoundError(agent_id)
            return agent

    def add(self, agent_name: str, agent_type: str, language_model_id: str) -> Agent:
        gen_id = uuid4()
        with self.session_factory() as session:
            agent = Agent(
                id=str(gen_id),
                is_active=True,
                created_at=datetime.now(),
                agent_name=agent_name,
                agent_type=agent_type,
                agent_summary="",
                language_model_id=language_model_id,
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def update_agent(self, agent_id: str, agent_name: str) -> Agent:
        with self.session_factory() as session:
            entity: Agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not entity:
                raise AgentNotFoundError(agent_id)

            entity.agent_name = agent_name
            session.commit()
            session.refresh(entity)
            return entity

    def delete_by_id(self, agent_id: str) -> None:
        with self.session_factory() as session:
            entity: Agent = (
                session.query(Agent)
                .filter(Agent.id == agent_id, Agent.is_active)
                .first()
            )
            if not entity:
                raise AgentNotFoundError(agent_id)

            entity.is_active = False
            session.commit()


class AgentNotFoundError(NotFoundError):
    entity_name: str = "Agent"


class AgentSettingRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self, agent_id: str) -> Iterator[AgentSetting]:
        with self.session_factory() as session:
            return (
                session.query(AgentSetting)
                .filter(AgentSetting.agent_id == agent_id)
                .all()
            )

    def add(self, agent_id: str, setting_key: str, setting_value: str) -> AgentSetting:
        gen_id = uuid4()
        with self.session_factory() as session:
            agent_setting = AgentSetting(
                id=str(gen_id),
                agent_id=agent_id,
                setting_key=setting_key,
                setting_value=setting_value,
            )
            session.add(agent_setting)
            session.commit()
            session.refresh(agent_setting)
            return agent_setting

    def update_by_key(
        self, agent_id: str, setting_key: str, setting_value: str
    ) -> AgentSetting:
        with self.session_factory() as session:
            entity: AgentSetting = (
                session.query(AgentSetting)
                .filter(
                    AgentSetting.agent_id == agent_id,
                    AgentSetting.setting_key == setting_key,
                )
                .first()
            )
            if not entity:
                raise AgentSettingNotFoundError(agent_id)

            entity.setting_value = setting_value
            session.commit()
            session.refresh(entity)
            return entity


class AgentSettingNotFoundError(NotFoundError):
    entity_name: str = "AgentSetting"
