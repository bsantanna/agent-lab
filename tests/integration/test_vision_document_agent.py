import os
from pathlib import Path
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestVisionDocumentAgent:
    def _create_agent(self, client):
        # create integration
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://api.x.ai/v1/",
                "api_key": os.environ["XAI_API_KEY"],
                "integration_type": "xai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        # create llm
        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "grok-2-vision",
            },
        )
        language_model_id = response_2.json()["id"]

        # create agent
        return client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "vision_document",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(self, client, message_content, attachment_id):
        create_agent_response = self._create_agent(client)
        agent_id = create_agent_response.json()["id"]

        return client.post(
            "/messages/post",
            json={
                "message_role": "human",
                "message_content": message_content,
                "agent_id": agent_id,
                "attachment_id": attachment_id,
            },
        )

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
    async def test_post_message(self, client):
        # given
        upload_filename = "vision_document_01.jpg"
        upload_response = self._upload_file(client, upload_filename, "image/jpeg")
        attachment_id = upload_response.json()["id"]
        message_content = "Can you describe the following image?"

        # when
        create_message_response = self._create_message(
            client, message_content, attachment_id
        )

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]
