import os
from pathlib import Path
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestVoiceMemosAgent:
    def _create_agent(self, client, agent_type="voice_memos"):
        # create integration
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://api.openai.com/v1/",
                "api_key": os.environ["OPENAI_API_KEY"],
                "integration_type": "openai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        # create llm
        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "o3-mini",
            },
        )
        language_model_id = response_2.json()["id"]

        # create agent
        return client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": agent_type,
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(
        self, client, message_content, agent_id=None, attachment_id=None
    ):
        if agent_id is None:
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
        upload_filename = "voice_memos_01_pt_BR.mp3"
        upload_response = self._upload_file(client, upload_filename, "audio/mp3")
        attachment_id = upload_response.json()["id"]
        message_content = "Analyse the given audio."

        # when
        create_message_response = self._create_message(
            client, message_content, attachment_id=attachment_id
        )

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

        # test coordinator react flow (no attachment => react flow)
        # given
        agent_id = response_dict["agent_id"]
        follow_up_message_content = "Who participated the meeting?"

        # when
        create_follow_up_message_response = self._create_message(
            client, follow_up_message_content, agent_id=agent_id
        )

        # then
        assert create_follow_up_message_response.status_code == 200
        response_dict = create_follow_up_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]
        assert "Aline" in response_dict["message_content"]


class TestFastVoiceMemosAgent(TestVoiceMemosAgent):

    @pytest.mark.asyncio
    async def test_post_message(self, client):
        # given
        create_agent_response = self._create_agent(client, agent_type="fast_voice_memos")
        agent_id = create_agent_response.json()["id"]
        upload_filename = "voice_memos_01_pt_BR.mp3"
        upload_response = self._upload_file(client, upload_filename, "audio/mp3")
        attachment_id = upload_response.json()["id"]
        message_content = "Analyse the given audio."

        # when
        create_message_response = self._create_message(
            client, message_content, attachment_id=attachment_id, agent_id=agent_id
        )

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]
        response_data = response_dict["response_data"]
        assert response_data["structured_report"] is not None
        assert response_data["structured_report"]["main_topic"] is not None
        assert response_data["structured_report"]["discussed_points"] is not None
        assert response_data["structured_report"]["decisions_taken"] is not None
        assert response_data["structured_report"]["next_steps"] is not None
        assert response_data["structured_report"]["action_points"] is not None
        assert response_data["structured_report"]["named_entities"] is not None
