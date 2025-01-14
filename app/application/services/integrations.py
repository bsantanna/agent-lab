from typing import Iterator

from app.domain.models import Integration
from app.domain.repositories.integrations import IntegrationRepository


class IntegrationService:
    def __init__(self, integration_repository: IntegrationRepository) -> None:
        self._repository: IntegrationRepository = integration_repository

    def get_integrations(self) -> Iterator[Integration]:
        return self._repository.get_all()

    def get_integration_by_id(self, integration_id: str) -> Integration:
        return self._repository.get_by_id(integration_id)

    def create_integration(
        self, integration_type: str, api_endpoint: str, api_key: str
    ) -> Integration:
        return self._repository.add(
            integration_type=integration_type,
            api_endpoint=api_endpoint,
            api_key=api_key,
        )

    def delete_integration_by_id(self, integration_id: str) -> None:
        return self._repository.delete_by_id(integration_id)
