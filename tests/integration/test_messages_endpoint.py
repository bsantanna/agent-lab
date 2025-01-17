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

    @pytest.mark.asyncio
    async def test_get_list(self, client):
        create_request = self._create_agent(client)
        agent_id = create_request.json()["id"]

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
