from contextlib import AbstractContextManager
from datetime import datetime
from uuid import uuid4

import hvac
from sqlalchemy.orm import Session
from typing_extensions import Callable, Iterator

from app.domain.exceptions.base import NotFoundError
from app.domain.models import Integration


class IntegrationRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        vault_client: hvac.Client,
    ) -> None:
        self.session_factory = session_factory
        self.vault_client = vault_client

    def get_all(self) -> Iterator[Integration]:
        with self.session_factory() as session:
            return session.query(Integration).filter(Integration.is_active).all()

    def get_by_id(self, integration_id: str) -> Integration:
        with self.session_factory() as session:
            integration = (
                session.query(Integration)
                .filter(Integration.id == integration_id, Integration.is_active)
                .first()
            )
            if not integration:
                raise IntegrationNotFoundError(integration_id)
            return integration

    def add(
        self, integration_type: str, api_endpoint: str, api_key: str
    ) -> Integration:
        gen_id = uuid4()
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"integration_{gen_id}",
            secret={"api_endpoint": api_endpoint, "api_key": api_key},
        )

        with self.session_factory() as session:
            integration = Integration(
                id=str(gen_id),
                created_at=datetime.now(),
                is_active=True,
                integration_type=integration_type,
            )
            session.add(integration)
            session.commit()
            session.refresh(integration)
            return integration

    def delete_by_id(self, integration_id: str) -> None:
        with self.session_factory() as session:
            entity: Integration = (
                session.query(Integration)
                .filter(Integration.id == integration_id, Integration.is_active)
                .first()
            )
            if not entity:
                raise IntegrationNotFoundError(integration_id)

            entity.is_active = False
            session.commit()


class IntegrationNotFoundError(NotFoundError):
    entity_name: str = "Integration"
