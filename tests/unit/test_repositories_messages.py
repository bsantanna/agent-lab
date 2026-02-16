from unittest.mock import MagicMock, patch

import pytest

from app.domain.models import Message
from app.domain.repositories.messages import (
    MessageNotFoundError,
    MessageRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    session = MagicMock()
    db.session.return_value.__enter__ = MagicMock(return_value=session)
    db.session.return_value.__exit__ = MagicMock(return_value=False)
    return db, session


class TestMessageRepository:
    def test_get_all(self, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        expected = [MagicMock(spec=Message)]
        session.query.return_value.filter.return_value.all.return_value = expected

        result = repo.get_all(agent_id="agent-1", schema="test_schema")

        assert result == expected

    def test_get_by_id_found(self, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        message = MagicMock(spec=Message)
        session.query.return_value.filter.return_value.first.return_value = message

        result = repo.get_by_id(message_id="msg-1", schema="test_schema")

        assert result == message

    def test_get_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(MessageNotFoundError):
            repo.get_by_id(message_id="nonexistent", schema="test_schema")

    @patch("app.domain.repositories.messages.uuid4")
    def test_add_basic(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            message_content="Hello",
            message_role="human",
            agent_id="agent-1",
            schema="test_schema",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    @patch("app.domain.repositories.messages.uuid4")
    def test_add_with_replies_to(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        mock_uuid.return_value = "generated-uuid"
        parent_msg = MagicMock(spec=Message)
        parent_msg.id = "parent-msg-id"

        repo.add(
            message_content="Reply",
            message_role="assistant",
            agent_id="agent-1",
            schema="test_schema",
            replies_to=parent_msg,
        )

        added = session.add.call_args[0][0]
        assert added.replies_to == "parent-msg-id"

    @patch("app.domain.repositories.messages.uuid4")
    def test_add_without_replies_to(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            message_content="Hello",
            message_role="human",
            agent_id="agent-1",
            schema="test_schema",
            replies_to=None,
        )

        added = session.add.call_args[0][0]
        assert added.replies_to is None

    @patch("app.domain.repositories.messages.uuid4")
    def test_add_with_response_data_and_attachment(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            message_content="Hello",
            message_role="assistant",
            agent_id="agent-1",
            schema="test_schema",
            response_data={"key": "value"},
            attachment_id="att-1",
        )

        added = session.add.call_args[0][0]
        assert added.response_data == {"key": "value"}
        assert added.attachment_id == "att-1"

    def test_delete_by_id_found(self, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        message = MagicMock(spec=Message)
        session.query.return_value.filter.return_value.first.return_value = message

        repo.delete_by_id(message_id="msg-1", schema="test_schema")

        assert message.is_active is False
        session.commit.assert_called_once()

    def test_delete_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = MessageRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(MessageNotFoundError):
            repo.delete_by_id(message_id="nonexistent", schema="test_schema")


class TestMessageNotFoundError:
    def test_entity_name(self):
        assert MessageNotFoundError.entity_name == "Message"

    def test_message(self):
        error = MessageNotFoundError("test-id")
        assert error.status_code == 404
        assert "Message" in error.detail
