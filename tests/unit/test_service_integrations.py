from unittest.mock import MagicMock

import pytest

from app.domain.models import Integration
from app.services.integrations import IntegrationService


@pytest.fixture
def integration_service():
    repo = MagicMock()
    service = IntegrationService(integration_repository=repo)
    return service, repo


class TestIntegrationService:
    def test_get_integrations(self, integration_service):
        service, repo = integration_service
        expected = [MagicMock(spec=Integration)]
        repo.get_all.return_value = expected

        result = service.get_integrations(schema="test")

        assert result == expected
        repo.get_all.assert_called_once_with("test")

    def test_get_integration_by_id(self, integration_service):
        service, repo = integration_service
        integration = MagicMock(spec=Integration)
        repo.get_by_id.return_value = integration

        result = service.get_integration_by_id(integration_id="int-1", schema="test")

        assert result == integration
        repo.get_by_id.assert_called_once_with("int-1", "test")

    def test_create_integration(self, integration_service):
        service, repo = integration_service
        integration = MagicMock(spec=Integration)
        repo.add.return_value = integration

        result = service.create_integration(
            integration_type="openai_api_v1",
            api_endpoint="https://api.openai.com",
            api_key="sk-test",
            schema="test",
        )

        assert result == integration
        repo.add.assert_called_once_with(
            integration_type="openai_api_v1",
            api_endpoint="https://api.openai.com",
            api_key="sk-test",
            schema="test",
        )

    def test_delete_integration_by_id(self, integration_service):
        service, repo = integration_service

        service.delete_integration_by_id(integration_id="int-1", schema="test")

        repo.delete_by_id.assert_called_once_with("int-1", "test")
