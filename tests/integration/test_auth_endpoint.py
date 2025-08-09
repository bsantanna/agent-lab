import pytest
from fastapi.testclient import TestClient

from app.core.container import Container
from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture
def container():
    cont = Container()
    cont.init_resources()
    yield cont


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_unauthorized(self, client):
        # when
        response = client.post(
            "/auth/login",
            json={"username": "foo", "password": "baz"},
        )

        # then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        # when
        response = client.post(
            "/auth/login",
            json={"username": "foo", "password": "bar"},
        )

        # then
        assert response.status_code == 201
        response_json = response.json()
        assert "access_token" in response_json
        assert "refresh_token" in response_json

    @pytest.mark.asyncio
    async def test_renew_unauthorized(self, client):
        # when
        response = client.post(
            "/auth/renew",
            json={"refresh_token": "invalid_refresh_token"},
        )

        # then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_renew_success(self, client):
        # given
        response = client.post(
            "/auth/login",
            json={"username": "foo", "password": "bar"},
        )
        valid_refresh_token = response.json()["refresh_token"]

        # when
        response = client.post(
            "/auth/renew",
            json={"refresh_token": valid_refresh_token},
        )

        # then
        assert response.status_code == 201
        response_json = response.json()
        assert "access_token" in response_json
        assert "refresh_token" in response_json
