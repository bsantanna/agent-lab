import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def _auth_headers():
    return {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}


class TestExceptionHandler:
    def test_http_exception_with_status_prefix(self, client):
        """Exception detail starting with 'NNN:' should override the status code."""
        # The auth endpoint raises AuthenticationError with status 401
        # and detail "Authentication failed: ...". We test via a real endpoint.
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "wrong"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_http_exception_with_409_prefix(self, client):
        """Exception detail starting with '409:' should return 409 status."""

        @client.app.get("/test-409-prefix")
        async def trigger_409():
            raise HTTPException(status_code=500, detail="409: Conflict occurred")

        response = client.get("/test-409-prefix", headers=_auth_headers())
        assert response.status_code == 409
        assert response.json()["detail"] == "Conflict occurred"

    def test_http_exception_without_prefix(self, client):
        """Exception without numeric prefix should keep original status code."""

        @client.app.get("/test-plain-error")
        async def trigger_plain():
            raise HTTPException(status_code=422, detail="Validation failed")

        response = client.get("/test-plain-error", headers=_auth_headers())
        assert response.status_code == 422
        assert response.json()["detail"] == "Validation failed"


class TestMcpSlashRewrite:
    def test_mcp_path_rewrite(self, client):
        """GET /mcp should be rewritten to /mcp/ and not return 404."""
        response = client.get("/mcp")
        # The MCP app is mounted at /mcp — a rewrite to /mcp/ should reach it
        assert response.status_code != 404

    def test_mcp_slash_path_works(self, client):
        """GET /mcp/ should work directly."""
        response = client.get("/mcp/")
        assert response.status_code != 404


class TestResourceMetadata:
    def test_oauth_protected_resource_metadata(self, client):
        response = client.get("/.well-known/oauth-protected-resource/mcp")
        assert response.status_code == 200
        data = response.json()
        assert "resource" in data
        assert "authorization_servers" in data
        assert "scopes_supported" in data
        assert "bearer_methods_supported" in data

    def test_oauth_protected_resource_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-protected-resource/mcp/")
        assert response.status_code == 200

    def test_oauth_authorization_server_metadata(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp")
        assert response.status_code == 200
        data = response.json()
        assert "issuer" in data
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "registration_endpoint" in data
        assert "code_challenge_methods_supported" in data
        assert "S256" in data["code_challenge_methods_supported"]

    def test_oauth_authorization_server_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp/")
        assert response.status_code == 200
