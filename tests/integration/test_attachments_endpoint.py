from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)

class TestAttachmentsEndpoint:
    def _upload_file(self, client, filename: str, content_type: str):
        current_dir = Path(__file__).parent
        file_path = f"{current_dir}/{filename}"

        # when
        with open(file_path, "rb") as file:
            upload_response = client.post(
                url="/attachments/upload",
                files={"file": (filename, file, content_type)},
            )

        return upload_response

    @pytest.mark.asyncio
    async def test_embeddings(self, client):
        # given
        upload_filename = "sun_tzu_the_art_of_war.zip"
        upload_response = self._upload_file(client, upload_filename, "application/zip")
        attachment_id = upload_response.json()["id"]

        # when



