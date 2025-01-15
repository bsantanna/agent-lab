import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestLanguageModelsEndpoint:
    def _create_language_model(self, client):
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

        return client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "an_invalid_tag",
            },
        )

    @pytest.mark.asyncio
    async def test_get_list(self, client):
        # when
        response = client.get("/llms/list")

        # then
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_and_get_by_id_success(self, client):
        # when
        create_response = self._create_language_model(client)

        # then
        assert create_response.status_code == 201
        assert "id" in create_response.json()

        # when
        entity_id = create_response.json()["id"]
        read_response = client.get(f"/llms/{entity_id}")

        # then
        assert read_response.status_code == 200
        assert "id" in read_response.json()
        assert "lm_settings" in read_response.json()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, client):
        # given
        integration_id = "not_existing_id"

        # when
        response = client.get(f"/llms/{integration_id}")

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_and_delete_success(self, client):
        # given
        create_response = self._create_language_model(client)

        # when
        language_model_id = create_response.json()["id"]
        delete_response = client.delete(f"/llms/delete/{language_model_id}")

        # then
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        # given
        language_model_id = "not_existing_id"

        # when
        response = client.delete(f"/llms/delete/{language_model_id}")

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_integration_id(self, client):
        # given
        response = client.post(
            url="/llms/create",
            json={
                "integration_id": "an_invalid_integration_id",
                "language_model_tag": "an_invalid_tag",
            },
        )

        # then
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_language_model_not_found(self, client):
        # given
        language_model_id = "not_existing_id"

        # when
        response = client.post(
            url="/llms/update",
            json={
                "language_model_id": language_model_id,
                "language_model_tag": "any_tag",
            },
        )

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_success(self, client):
        # given
        create_response = self._create_language_model(client)
        language_model_id = create_response.json()["id"]

        # when
        update_response = client.post(
            url="/llms/update",
            json={
                "language_model_id": language_model_id,
                "language_model_tag": "another_tag",
            },
        )

        # then
        assert update_response.status_code == 200
        assert "id" in update_response.json()
        assert "another_tag" == update_response.json()["language_model_tag"]

    @pytest.mark.asyncio
    async def test_update_setting_language_model_not_found(self, client):
        # given
        language_model_id = "not_existing_id"

        # when
        response = client.post(
            url="/llms/update_setting",
            json={
                "language_model_id": language_model_id,
                "setting_key": "a_key",
                "setting_value": "a_value",
            },
        )

        # then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_setting_key_not_found(self, client):
        # given
        create_response = self._create_language_model(client)
        language_model_id = create_response.json()["id"]

        # when
        update_response = client.post(
            url="/llms/update_setting",
            json={
                "language_model_id": language_model_id,
                "setting_key": "a_key",
                "setting_value": "a_value",
            },
        )

        # then
        assert update_response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_setting_success(self, client):
        # given
        client_response = self._create_language_model(client)
        language_model_id = client_response.json()["id"]

        # when
        update_response = client.post(
            url="/llms/update_setting",
            json={
                "language_model_id": language_model_id,
                "setting_key": "temperature",
                "setting_value": "0.9",
            },
        )

        # then
        assert update_response.status_code == 200
        assert "id" in update_response.json()
        assert "0.9" == update_response.json()["lm_settings"][0]["setting_value"]
