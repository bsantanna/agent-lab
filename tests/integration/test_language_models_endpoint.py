import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestLanguageModelsEndpoint:
    @pytest.mark.asyncio
    async def test_get_list(self, client):
        # when
        response = client.get("/llms/list")

        # then
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_and_get_by_id_success(self, client):
        # given
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://example.com",
                "api_key": "an_invalid_key",
                "integration_type": "openai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        # when
        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "an_invalid_tag",
            },
        )

        # then
        assert response_2.status_code == 201
        assert "id" in response_2.json()

        # when
        language_model_id = response_2.json()["id"]
        response_3 = client.get(f"/llms/{language_model_id}")

        # then
        assert response_3.status_code == 200
        assert "id" in response_3.json()
        assert "lm_settings" in response_3.json()

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
        response = client.post(
            url="/integrations/create",
            json={
                "api_endpoint": "https://example.com",
                "api_key": "an_invalid_key",
                "integration_type": "openai_api_v1",
            },
        )
        integration_id = response.json()["id"]

        response_2 = client.post(
            url="/llms/create",
            json={
                "integration_id": integration_id,
                "language_model_tag": "an_invalid_tag",
            },
        )

        # when
        language_model_id = response_2.json()["id"]
        response_3 = client.delete(f"/llms/delete/{language_model_id}")

        # then
        assert response_3.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        # given
        integration_id = "not_existing_id"

        # when
        response = client.delete(f"/llms/delete/{integration_id}")

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
