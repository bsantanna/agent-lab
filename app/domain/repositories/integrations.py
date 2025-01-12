from contextlib import AbstractContextManager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Integration


class IntegrationRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        self.session_factory = session_factory

    def get_all(self) -> Iterator[Integration]:
        with self.session_factory() as session:
            return session.query(Integration).all()

    def get_by_id(self, integration_id: int) -> Integration:
        with self.session_factory() as session:
            integration = (
                session.query(Integration)
                .filter(Integration.id == integration_id)
                .first()
            )
            if not integration:
                raise IntegrationNotFoundError(integration_id)
            return integration

    def add(self, email: str, password: str, is_active: bool = True) -> Integration:
        with self.session_factory() as session:
            integration = Integration(
                email=email, hashed_password=password, is_active=is_active
            )
            session.add(integration)
            session.commit()
            session.refresh(integration)
            return integration

    def delete_by_id(self, integration_id: int) -> None:
        with self.session_factory() as session:
            entity: Integration = (
                session.query(Integration)
                .filter(Integration.id == integration_id)
                .first()
            )
            if not entity:
                raise IntegrationNotFoundError(integration_id)
            session.delete(entity)
            session.commit()


class IntegrationNotFoundError(NotFoundError):
    entity_name: str = "Integration"
