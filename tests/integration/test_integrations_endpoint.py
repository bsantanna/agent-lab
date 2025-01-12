import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


# class TestAgentsEndpoints:
#     @pytest.mark.asyncio
#     async def test_get_list(self, client):
#         # when
#         response = client.get("/agents/list")
#
#         # then
#         assert response.status_code == 200
#         assert isinstance(response.json(), list)
#
#     @pytest.mark.asyncio
#     async def test_get_by_id_success(self, client):
#         # given
#         response = client.post("/agents/create")
#         agent_id = response.json()["id"]
#
#         # when
#         response_2 = client.get(f"/agents/{agent_id}")
#
#         # then
#         assert response_2.status_code == 200
#         assert "id" in response_2.json()
#
#     @pytest.mark.asyncio
#     async def test_get_by_id_not_found(self, client):
#         # given
#         agent_id = 9999
#
#         # when
#         response = client.get(f"/agents/{agent_id}")
#
#         # then
#         assert response.status_code == 404
#
#     @pytest.mark.asyncio
#     async def test_add_item(self, client):
#         # when
#         response = client.post("/agents/create")
#
#         # then
#         assert response.status_code == 201
#         assert "id" in response.json()
#
#     @pytest.mark.asyncio
#     async def test_remove_agent_success(self, client):
#         # given
#         response = client.post("/agents/create")
#         agent_id = response.json()["id"]
#
#         # when
#         response_2 = client.delete(f"/agents/delete/{agent_id}")
#
#         # then
#         assert response_2.status_code == 204
#
#     @pytest.mark.asyncio
#     async def test_remove_agent_not_found(self, client):
#         # given
#         agent_id = 9999
#
#         # when
#         response = client.delete(f"/agents/delete/{agent_id}")
#
#         # then
#         assert response.status_code == 404
