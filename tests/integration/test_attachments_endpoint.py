import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestAttachmentsEndpoint:
    def _create_embeddings(
        self, client, attachment_id, language_model_id, collection_name
    ):
        return client.post(
            url="/attachments/embeddings",
            json={
                "attachment_id": attachment_id,
                "language_model_id": language_model_id,
                "collection_name": collection_name,
            },
        )

    def _create_llm(self, client):
        # create integration
        response = client.post(
            url="/integrations/create",
            json={
                "integration_type": "ollama_api_v1",
                "api_endpoint": os.getenv("OLLAMA_ENDPOINT"),
                "api_key": "ollama",
            },
        )
        integration_id = response.json()["id"]

        # create llm
        return client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "phi3",
            },
        )

    def _upload_file(self, client, filename: str, content_type: str):
        current_dir = Path(__file__).parent
        file_path = f"{current_dir}/{filename}"

        with open(file_path, "rb") as file:
            upload_response = client.post(
                url="/attachments/upload",
                files={"file": (filename, file, content_type)},
            )

        return upload_response

    @pytest.mark.asyncio
    async def test_embeddings(self, client):
        # given
        upload_filename = "attachment.zip"
        upload_response = self._upload_file(client, upload_filename, "application/zip")
        attachment_id = upload_response.json()["id"]

        llm_response = self._create_llm(client)
        llm_id = llm_response.json()["id"]

        # when
        response = self._create_embeddings(
            client, attachment_id, llm_id, "static_document_data"
        )

        # then
        assert response.status_code == 201
        embeddings_response = response.json()
        assert embeddings_response["embeddings_collection"] == "static_document_data"
