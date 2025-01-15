from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestAgentsEndpoints:
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
                "agent_type": "three_phase_react",
                "agent_name": f"agent-{uuid4()}",
            },
        )

    @pytest.mark.asyncio
    async def test_get_list(self, client):
        # when
        response = client.get("/agents/list")

        # then
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_and_read_success(self, client):
        # given
        create_agent_response = self._create_agent(client)
        agent_id = create_agent_response.json()["id"]

        # when
        read_agent_response = client.get(f"/agents/{agent_id}")

        # then
        assert read_agent_response.status_code == 200
        response_json = read_agent_response.json()
        assert "ag_settings" in response_json
        assert isinstance(response_json["ag_settings"], list)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, client):
        # given
        agent_id = "not_existing_id"

        # when
        response = client.get(f"/agents/{agent_id}")

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_and_delete_success(self, client):
        # given
        create_agent_response = self._create_agent(client)
        agent_id = create_agent_response.json()["id"]

        # when
        delete_agent_response = client.delete(f"/agents/delete/{agent_id}")

        # then
        assert delete_agent_response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        # given
        agent_id = "not_existing_id"

        # when
        response = client.delete(f"/agents/delete/{agent_id}")

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_agent_type_bad_request(self, client):
        # given
        create_agent_response = self._create_agent(client)
        language_model_id = create_agent_response.json()["language_model_id"]

        # when
        error_response = client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "an_invalid_agent_type",
                "agent_name": f"agent-{uuid4()}",
            },
        )

        # then
        assert error_response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_invalid_language_model_bas_request(self, client):
        # given
        language_model_id = "an_invalid_language_model_id"

        # when
        error_response = client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "three_phase_react",
                "agent_name": f"agent-{uuid4()}",
            },
        )

        # then
        assert error_response.status_code == 400
