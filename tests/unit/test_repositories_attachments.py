from unittest.mock import MagicMock, patch

import pytest

from app.domain.models import Attachment
from app.domain.repositories.attachments import (
    AttachmentNotFoundError,
    AttachmentRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    session = MagicMock()
    db.session.return_value.__enter__ = MagicMock(return_value=session)
    db.session.return_value.__exit__ = MagicMock(return_value=False)
    return db, session


class TestAttachmentRepository:
    def test_get_all(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        expected = [MagicMock(spec=Attachment), MagicMock(spec=Attachment)]
        session.query.return_value.filter.return_value.all.return_value = expected

        result = repo.get_all(schema="test_schema")

        assert result == expected
        assert len(result) == 2
        db.session.assert_called_once_with(schema_name="test_schema")

    def test_get_all_empty(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        session.query.return_value.filter.return_value.all.return_value = []

        result = repo.get_all(schema="test_schema")

        assert result == []

    def test_get_by_id_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        attachment = MagicMock(spec=Attachment)
        session.query.return_value.filter.return_value.first.return_value = attachment

        result = repo.get_by_id(attachment_id="att-1", schema="test_schema")

        assert result == attachment

    def test_get_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(AttachmentNotFoundError):
            repo.get_by_id(attachment_id="nonexistent", schema="test_schema")

    @patch("app.domain.repositories.attachments.uuid4")
    def test_add_without_id(self, mock_uuid, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        mock_uuid.return_value = "generated-uuid"

        repo.add(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            schema="test_schema",
        )

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_add_with_id(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)

        repo.add(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            schema="test_schema",
            attachment_id="custom-id",
        )

        session.add.assert_called_once()
        added = session.add.call_args[0][0]
        assert added.id == "custom-id"

    def test_delete_by_id_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        attachment = MagicMock(spec=Attachment)
        session.query.return_value.filter.return_value.first.return_value = attachment

        repo.delete_by_id(attachment_id="att-1", schema="test_schema")

        session.delete.assert_called_once_with(attachment)
        session.commit.assert_called_once()

    def test_delete_by_id_not_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(AttachmentNotFoundError):
            repo.delete_by_id(attachment_id="nonexistent", schema="test_schema")

    def test_update_attachment_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        attachment = MagicMock(spec=Attachment)
        session.query.return_value.filter.return_value.first.return_value = attachment

        repo.update_attachment(
            attachment_id="att-1",
            embeddings_collection="my_collection",
            schema="test_schema",
        )

        assert attachment.embeddings_collection == "my_collection"
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_update_attachment_not_found(self, mock_db):
        db, session = mock_db
        repo = AttachmentRepository(db=db)
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(AttachmentNotFoundError):
            repo.update_attachment(
                attachment_id="nonexistent",
                embeddings_collection="my_collection",
                schema="test_schema",
            )


class TestAttachmentNotFoundError:
    def test_entity_name(self):
        assert AttachmentNotFoundError.entity_name == "Attachment"

    def test_message(self):
        error = AttachmentNotFoundError("test-id")
        assert error.status_code == 404
        assert "Attachment" in error.detail
