from typing_extensions import Iterator

from app.domain.models import Integration
from app.domain.repositories.integrations import IntegrationRepository


class IntegrationService:
    def __init__(self, integration_repository: IntegrationRepository) -> None:
        self.repository: IntegrationRepository = integration_repository

    def get_integrations(self, schema: str) -> Iterator[Integration]:
        return self.repository.get_all(schema)

    def get_integration_by_id(self, integration_id: str, schema: str) -> Integration:
        return self.repository.get_by_id(integration_id, schema)

    def create_integration(
        self, integration_type: str, api_endpoint: str, api_key: str, schema: str
    ) -> Integration:
        return self.repository.add(
            integration_type=integration_type,
            api_endpoint=api_endpoint,
            api_key=api_key,
            schema=schema,
        )

    def delete_integration_by_id(self, integration_id: str, schema: str) -> None:
        return self.repository.delete_by_id(integration_id, schema)
