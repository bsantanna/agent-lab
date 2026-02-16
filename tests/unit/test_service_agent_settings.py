from unittest.mock import MagicMock

import pytest

from app.domain.models import AgentSetting
from app.services.agent_settings import AgentSettingService


@pytest.fixture
def setting_service():
    repo = MagicMock()
    service = AgentSettingService(agent_setting_repository=repo)
    return service, repo


class TestAgentSettingService:
    def test_get_agent_settings(self, setting_service):
        service, repo = setting_service
        expected = [MagicMock(spec=AgentSetting)]
        repo.get_all.return_value = expected

        result = service.get_agent_settings(agent_id="agent-1", schema="test")

        assert result == expected
        repo.get_all.assert_called_once_with("agent-1", "test")

    def test_create_agent_setting(self, setting_service):
        service, repo = setting_service
        setting = MagicMock(spec=AgentSetting)
        repo.add.return_value = setting

        result = service.create_agent_setting(
            agent_id="agent-1",
            setting_key="prompt",
            setting_value="Hello",
            schema="test",
        )

        assert result == setting
        repo.add.assert_called_once_with(
            agent_id="agent-1",
            setting_key="prompt",
            setting_value="Hello",
            schema="test",
        )

    def test_update_by_key(self, setting_service):
        service, repo = setting_service
        setting = MagicMock(spec=AgentSetting)
        repo.update_by_key.return_value = setting

        result = service.update_by_key(
            agent_id="agent-1",
            setting_key="prompt",
            setting_value="Updated",
            schema="test",
        )

        assert result == setting
        repo.update_by_key.assert_called_once_with(
            agent_id="agent-1",
            setting_key="prompt",
            setting_value="Updated",
            schema="test",
        )
