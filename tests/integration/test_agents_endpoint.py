import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestAgentsEndpoints:
    @pytest.mark.asyncio
    async def test_get_list(self, client):
        response = client.get("/agents/list")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, client):
        response = client.post("/agents/create")
        assert response.status_code == 201
        user_id = response.json()["id"]
        response_2 = client.get(f"/agents/{user_id}")
        assert response_2.status_code == 200
        assert "id" in response_2.json()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, client):
        user_id = 9999
        response = client.get(f"/agents/{user_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_user(self, client):
        response = client.post("/agents/create")
        assert response.status_code == 201
        assert "id" in response.json()

    @pytest.mark.asyncio
    async def test_remove_user_success(self, client):
        response = client.post("/agents/create")
        assert response.status_code == 201
        user_id = response.json()["id"]
        response_2 = client.delete(f"/agents/delete/{user_id}")
        assert response_2.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_user_not_found(self, client):
        user_id = 9999
        response = client.delete(f"/agents/delete/{user_id}")
        assert response.status_code == 404
