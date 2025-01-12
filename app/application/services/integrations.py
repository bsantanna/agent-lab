from typing import Iterator
from uuid import uuid4

from app.domain.models import Integration
from app.domain.repositories.integrations import IntegrationRepository


class IntegrationService:
    def __init__(self, integration_repository: IntegrationRepository) -> None:
        self._repository: IntegrationRepository = integration_repository

    def get_integrations(self) -> Iterator[Integration]:
        return self._repository.get_all()

    def get_integration_by_id(self, integration_id: int) -> Integration:
        return self._repository.get_by_id(integration_id)

    def create_integration(self) -> Integration:
        uid = uuid4()
        return self._repository.add(email=f"{uid}@email.com", password="pwd")

    def delete_integration_by_id(self, integration_id: int) -> None:
        return self._repository.delete_by_id(integration_id)
