import os
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestCoordinatorPlannerSupervisorAgent:
    def _create_agent(self, client):
        # create integration
        response = client.post(
            url="/integrations/create",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
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
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            json={
                "integration_id": integration_id,
                "language_model_tag": "grok-code-fast",
            },
        )
        language_model_id = response_2.json()["id"]

        # create agent
        return client.post(
            url="/agents/create",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            json={
                "language_model_id": language_model_id,
                "agent_type": "coordinator_planner_supervisor",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(self, client, message_content, agent_id=None):
        if agent_id is None:
            create_agent_response = self._create_agent(client)
            agent_id = create_agent_response.json()["id"]

        return client.post(
            "/messages/post",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            json={
                "message_role": "human",
                "message_content": message_content,
                "agent_id": agent_id,
            },
        )

    @pytest.mark.asyncio
    async def test_researcher(self, client):
        # given
        message_content = "According to Sun Tzu, what is the pinnacle of excellence?"

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

    @pytest.mark.asyncio
    async def test_coder(self, client):
        # given
        message_content = (
            "Please create a hello world in Python that accepts a name parameter."
        )

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

        # convert previous code response to bash
        # when
        agent_id = response_dict["agent_id"]
        follow_up_message_content = "Please convert previous code to bash."

        # when
        create_follow_up_message_response = self._create_message(
            client, follow_up_message_content, agent_id=agent_id
        )

        # then
        assert create_follow_up_message_response.status_code == 200
        response_dict = create_follow_up_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

    @pytest.mark.asyncio
    async def test_browser(self, client):
        # given
        message_content = (
            "Visit https://agent-lab.btech.software/docs and list all http methods, "
            "endpoints and description as a markdown table, print the markdown table "
            "(do not generate files)."
        )

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]
