from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.container import Container
from app.main import app
from app.services.tasks import TaskProgress


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture
def container():
    cont = Container()
    cont.init_resources()
    yield cont


class TestAgentsEndpoints:
    def _create_integration(self, client):
        # create integration
        return client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://example.com",
                "api_key": "an_invalid_key",
                "integration_type": "openai_api_v1",
            },
        )

    def _create_language_model(self, client, integration_id):
        # create llm
        return client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "an_invalid_tag",
            },
        )

    def _create_agent(self, client):
        # create integration
        response = self._create_integration(client)
        integration_id = response.json()["id"]

        # create llm
        response_2 = self._create_language_model(client, integration_id)
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
    async def test_create_invalid_language_model_not_found(self, client):
        # given
        language_model_id = "an_invalid_language_model_id"

        # when
        error_response = client.post(
            url="/agents/create",
            json={
                "language_model_id": language_model_id,
                "agent_type": "test_echo",
                "agent_name": f"agent-{uuid4()}",
            },
        )

        # then
        assert error_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_unprocessable_entity(self, client):
        # when
        error_response = client.post(
            url="/agents/create",
            json={"foo": "bar"},
        )

        # then
        assert error_response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_invalid_unprocessable_entity(self, client):
        # when
        error_response = client.post(
            url="/agents/update",
            json={"foo": "bar"},
        )

        # then
        assert error_response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, client):
        # given
        response = self._create_integration(client)
        integration_id = response.json()["id"]
        response_2 = self._create_language_model(client, integration_id)
        language_model_id = response_2.json()["id"]

        agent_id = "not_existing_id"

        # when
        response = client.post(
            url="/agents/update",
            json={
                "agent_id": agent_id,
                "agent_name": "a_name",
                "language_model_id": language_model_id,
            },
        )

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_language_model_not_found(self, client):
        # given
        create_response = self._create_agent(client)
        agent_id = create_response.json()["id"]

        # when
        update_response = client.post(
            url="/agents/update",
            json={
                "agent_id": agent_id,
                "agent_name": "a_modified_name",
                "language_model_id": "not_existing_language_model_id",
            },
        )

        # then
        assert update_response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_invalid_agent_name_bad_request(self, client):
        # given
        create_response = self._create_agent(client)
        agent_id = create_response.json()["id"]
        language_model_id = create_response.json()["language_model_id"]

        # when
        update_response = client.post(
            url="/agents/update",
            json={
                "agent_id": agent_id,
                "agent_name": "a modified_name",
                "language_model_id": language_model_id,
            },
        )

        # then
        assert update_response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_success(self, client):
        # given
        create_response = self._create_agent(client)
        agent_id = create_response.json()["id"]
        language_model_id = create_response.json()["language_model_id"]

        # when
        update_response = client.post(
            url="/agents/update",
            json={
                "agent_id": agent_id,
                "agent_name": "a_modified_name",
                "language_model_id": language_model_id,
            },
        )

        # then
        assert update_response.status_code == 200
        assert "id" in update_response.json()
        assert "a_modified_name" == update_response.json()["agent_name"]

    @pytest.mark.asyncio
    async def test_update_setting_not_found(self, client):
        # given
        agent_id = "not_existing_id"

        # when
        response = client.post(
            url="/agents/update_setting",
            json={
                "agent_id": agent_id,
                "setting_key": "a_key",
                "setting_value": "a_value",
            },
        )

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_setting_key_not_found(self, client):
        # given
        create_response = self._create_agent(client)
        agent_id = create_response.json()["id"]

        # when
        update_response = client.post(
            url="/agents/update_setting",
            json={
                "agent_id": agent_id,
                "setting_key": "a_key",
                "setting_value": "a_value",
            },
        )

        # then
        assert update_response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_setting_success(self, client):
        # given
        client_response = self._create_agent(client)
        agent_id = client_response.json()["id"]

        # when
        update_response = client.post(
            url="/agents/update_setting",
            json={
                "agent_id": agent_id,
                "setting_key": "dummy_setting",
                "setting_value": "another_dummy_value",
            },
        )

        # then
        assert update_response.status_code == 200
        response_json = update_response.json()
        assert "id" in response_json
        assert any(
            setting["setting_value"] == "another_dummy_value"
            for setting in response_json["ag_settings"]
        )

    @pytest.mark.asyncio
    async def test_task_notification_websocket_receives_messages(
        self, client, container
    ):
        # Use a test agent id to match the filter inside the endpoint
        test_agent_id = "test_agent"
        ws_url = f"/agents/ws/task_updates/{test_agent_id}"

        with client.websocket_connect(ws_url, timeout=10) as websocket:
            task_notification_service = container.task_notification_service()
            task_notification_service.subscribe()
            test_update = TaskProgress(
                agent_id=test_agent_id,
                status="in_progress",
                message_content="Test Message",
            )
            task_notification_service.publish_update(test_update)

            # The endpoint should receive and send back the published message.
            received = websocket.receive_json()
            assert received["agent_id"] == test_agent_id
            assert received["message_content"] == "Test Message"
            websocket.close()
