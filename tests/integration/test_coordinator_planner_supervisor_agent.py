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
                "agent_type": "coordinator_planner_supervisor",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    def _create_message(self, client, message_content):
        create_agent_response = self._create_agent(client)
        agent_id = create_agent_response.json()["id"]

        return client.post(
            "/messages/post",
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
            "Please create a hello world in Python that accepts a name parameter. "
            "What would be the result of calling the function with name='Bruno'?"
        )

        # when
        create_message_response = self._create_message(client, message_content)

        # then
        assert create_message_response.status_code == 200
        response_dict = create_message_response.json()
        assert "id" in response_dict
        assert "assistant" == response_dict["message_role"]

    # @pytest.mark.asyncio
    # async def test_browser(self, client):
    #     # given
    #     message_content = "Go to https://github.com/bsantanna/agent-lab and generate a overview about the project."
    #
    #     # when
    #     create_message_response = self._create_message(client, message_content)
    #
    #     # then
    #     assert create_message_response.status_code == 200
    #     response_dict = create_message_response.json()
    #     assert "id" in response_dict
    #     assert "assistant" == response_dict["message_role"]
