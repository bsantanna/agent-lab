from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestMessagesEndpoints:
    def _create_agent(self, client):
        # create integration
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://example.com",
                "api_key": "an_invalid_key",
                "integration_type": "openai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        # create llm
        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "an_invalid_tag",
            },
        )
        language_model_id = response_2.json()["id"]

        # create agent
        return client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "test_echo",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(self, client, attachment_id: str = None):
        create_agent_response = self._create_agent(client)
        agent_id = create_agent_response.json()["id"]

        return client.post(
            "/messages/post",
            json={
                "message_role": "human",
                "message_content": "a_message",
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
    async def test_get_list(self, client):
        create_response = self._create_agent(client)
        agent_id = create_response.json()["id"]

        # when
        response = client.post(url="/messages/list", json={"agent_id": agent_id})

        # then
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_list_error_agent_bad_request(self, client):
        agent_id = "unknown"

        # when
        response = client.post(url="/messages/list", json={"agent_id": agent_id})

        # then
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_post_message(self, client):
        # when
        create_message_response = self._create_message(client)

        # then
        assert create_message_response.status_code == 200
        assert "id" in create_message_response.json()
        assert "assistant" == create_message_response.json()["message_role"]

    @pytest.mark.asyncio
    async def test_post_message_error_agent_not_found(self, client):
        agent_id = "unknown"

        # when
        response = client.post(
            url="/messages/post",
            json={
                "message_role": "human",
                "message_content": "a_message",
                "agent_id": agent_id,
                "attachment_id": None,
            },
        )
        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_and_read_message_with_attachment(self, client):
        # given
        upload_filename = "sun_tzu_the_art_of_war.zip"
        upload_response = self._upload_file(client, upload_filename, "application/zip")
        attachment_id = upload_response.json()["id"]

        # when
        create_message_response = self._create_message(client, attachment_id)
        message_id = create_message_response.json()["id"]

        # then
        assert create_message_response.status_code == 200
        assert "assistant" == create_message_response.json()["message_role"]

        # also
        get_message_response = client.get(f"/messages/{message_id}")
        message_response_json = get_message_response.json()

        # then
        assert get_message_response.status_code == 200
        assert upload_filename == message_response_json["attachment"]["file_name"]
        assert message_response_json["attachment"]["parsed_content"] is not None

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, client):
        # given
        message_id = "unknown"

        # when
        response = client.get(f"/messages/{message_id}")

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_with_attachment_and_delete_success(self, client):
        # given
        upload_filename = "sun_tzu_the_art_of_war.zip"
        upload_response = self._upload_file(client, upload_filename, "application/zip")
        attachment_id = upload_response.json()["id"]
        create_message_response = self._create_message(client, attachment_id)
        message_id = create_message_response.json()["id"]

        # when
        delete_message_response = client.delete(f"/messages/delete/{message_id}")

        # then
        assert delete_message_response.status_code == 204
