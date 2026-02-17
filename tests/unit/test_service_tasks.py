from unittest.mock import MagicMock, patch

import pytest

from app.services.tasks import TaskNotificationService, TaskProgress


class TestTaskProgress:
    def test_create_in_progress(self):
        tp = TaskProgress(
            agent_id="agent-1",
            status="in_progress",
        )
        assert tp.agent_id == "agent-1"
        assert tp.status == "in_progress"
        assert tp.message_content is None
        assert tp.response_data is None

    def test_create_completed(self):
        tp = TaskProgress(
            agent_id="agent-1",
            status="completed",
            message_content="Done",
            response_data={"key": "value"},
        )
        assert tp.status == "completed"
        assert tp.message_content == "Done"
        assert tp.response_data == {"key": "value"}

    def test_create_failed(self):
        tp = TaskProgress(agent_id="agent-1", status="failed")
        assert tp.status == "failed"

    def test_invalid_status(self):
        with pytest.raises(Exception):
            TaskProgress(agent_id="agent-1", status="invalid_status")

    def test_model_dump_json(self):
        tp = TaskProgress(
            agent_id="agent-1",
            status="completed",
            message_content="Done",
        )
        json_str = tp.model_dump_json()
        assert "agent-1" in json_str
        assert "completed" in json_str
        assert "Done" in json_str


class TestTaskNotificationService:
    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_init_default_channel(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(redis_url="redis://localhost:6379")

        assert service.channel == "task_updates"
        mock_redis_from_url.assert_called_once_with("redis://localhost:6379")

    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_init_custom_channel(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(
            redis_url="redis://localhost:6379", channel="custom_channel"
        )

        assert service.channel == "custom_channel"

    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_publish_update(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(redis_url="redis://localhost:6379")
        tp = TaskProgress(agent_id="agent-1", status="completed")

        service.publish_update(tp)

        mock_client.publish.assert_called_once_with(
            "task_updates", tp.model_dump_json()
        )

    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_subscribe(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(redis_url="redis://localhost:6379")
        service.subscribe()

        mock_pubsub.subscribe.assert_called_once_with("task_updates")

    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_listen(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.listen.return_value = iter([{"type": "message", "data": b"test"}])
        mock_client.pubsub.return_value = mock_pubsub
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(redis_url="redis://localhost:6379")
        result = service.listen()

        assert result is not None

    @patch("app.services.tasks.redis.StrictRedis.from_url")
    def test_close(self, mock_redis_from_url):
        mock_client = MagicMock()
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        mock_redis_from_url.return_value = mock_client

        service = TaskNotificationService(redis_url="redis://localhost:6379")
        service.close()

        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()
        mock_client.close.assert_called_once()
