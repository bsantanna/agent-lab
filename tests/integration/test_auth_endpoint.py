import os

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

    @pytest.mark.asyncio
    async def test_exchange_invalid_code(self, client):
        # when
        response = client.post(
            "/auth/exchange",
            json={
                "code": "invalid-code",
                "code_verifier": "some-verifier",
                "redirect_uri": "http://localhost/callback",
            },
        )

        # then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_profile_success(self, client):
        # when
        response = client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        )

        # then
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["username"] == "foo"
        assert response_json["email"] == "foo@bar.com"
        assert response_json["first_name"] == "Test"
        assert response_json["last_name"] == "User"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client):
        # when
        response = client.get("/auth/profile")

        # then
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_profile_success(self, client):
        # when
        response = client.put(
            "/auth/profile",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            json={
                "username": "foo",
                "email": "foo@bar.com",
                "first_name": "Updated",
                "last_name": "Name",
            },
        )

        # then
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["first_name"] == "Updated"
        assert response_json["last_name"] == "Name"

        # restore original values
        client.put(
            "/auth/profile",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            json={
                "username": "foo",
                "email": "foo@bar.com",
                "first_name": "Test",
                "last_name": "User",
            },
        )

    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self, client):
        # when
        response = client.put(
            "/auth/profile",
            json={
                "username": "foo",
                "email": "foo@bar.com",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        # then
        assert response.status_code == 403
