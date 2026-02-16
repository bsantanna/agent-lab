from unittest.mock import MagicMock

import pytest

from app.domain.models import Attachment
from app.services.attachments import AttachmentService


@pytest.fixture
def attachment_service():
    attachment_repo = MagicMock()
    document_repo = MagicMock()
    lm_service = MagicMock()
    lm_setting_service = MagicMock()
    integration_service = MagicMock()
    vault_client = MagicMock()
    service = AttachmentService(
        attachment_repository=attachment_repo,
        document_repository=document_repo,
        language_model_service=lm_service,
        language_model_setting_service=lm_setting_service,
        integration_service=integration_service,
        vault_client=vault_client,
    )
    return (
        service,
        attachment_repo,
        document_repo,
        lm_service,
        lm_setting_service,
        integration_service,
        vault_client,
    )


class TestAttachmentService:
    def test_get_attachments(self, attachment_service):
        service, repo, *_ = attachment_service
        expected = [MagicMock(spec=Attachment), MagicMock(spec=Attachment)]
        repo.get_all.return_value = expected

        result = service.get_attachments(schema="test")

        assert result == expected
        assert len(result) == 2
        repo.get_all.assert_called_once_with("test")

    def test_get_attachments_empty(self, attachment_service):
        service, repo, *_ = attachment_service
        repo.get_all.return_value = []

        result = service.get_attachments(schema="test")

        assert result == []

    def test_get_attachment_by_id(self, attachment_service):
        service, repo, *_ = attachment_service
        attachment = MagicMock(spec=Attachment)
        repo.get_by_id.return_value = attachment

        result = service.get_attachment_by_id(attachment_id="att-1", schema="test")

        assert result == attachment
        repo.get_by_id.assert_called_once_with("att-1", "test")

    def test_create_attachment_with_content(self, attachment_service):
        service, repo, *_ = attachment_service
        attachment = MagicMock(spec=Attachment)
        repo.add.return_value = attachment

        result = service.create_attachment_with_content(
            file_name="test.pdf",
            raw_content=b"raw bytes",
            parsed_content="parsed text",
            schema="test",
        )

        assert result == attachment
        repo.add.assert_called_once_with(
            file_name="test.pdf",
            raw_content=b"raw bytes",
            parsed_content="parsed text",
            attachment_id=None,
            schema="test",
        )

    def test_create_attachment_with_content_and_id(self, attachment_service):
        service, repo, *_ = attachment_service
        attachment = MagicMock(spec=Attachment)
        repo.add.return_value = attachment

        result = service.create_attachment_with_content(
            file_name="test.pdf",
            raw_content=b"raw bytes",
            parsed_content="parsed text",
            schema="test",
            attachment_id="custom-id",
        )

        assert result == attachment
        repo.add.assert_called_once_with(
            file_name="test.pdf",
            raw_content=b"raw bytes",
            parsed_content="parsed text",
            attachment_id="custom-id",
            schema="test",
        )

    def test_delete_attachment_by_id(self, attachment_service):
        service, repo, *_ = attachment_service

        service.delete_attachment_by_id(attachment_id="att-1", schema="test")

        repo.delete_by_id.assert_called_once_with("att-1", "test")
