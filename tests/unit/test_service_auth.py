from unittest.mock import MagicMock, patch

import pytest
import requests

from app.domain.exceptions.base import AuthenticationError
from app.interface.api.auth.schema import AuthResponse
from app.services.auth import AuthService


@pytest.fixture
def auth_service():
    return AuthService(
        enabled=True,
        url="http://keycloak:8080",
        realm="test-realm",
        client_id="test-client",
        client_secret="test-secret",
    )


class TestAuthService:
    def test_init(self, auth_service):
        assert auth_service.enabled is True
        assert auth_service.url == "http://keycloak:8080"
        assert auth_service.realm == "test-realm"
        assert auth_service.client_id == "test-client"
        assert auth_service.client_secret == "test-secret"
        assert (
            auth_service.token_url
            == "http://keycloak:8080/realms/test-realm/protocol/openid-connect/token"
        )

    @patch("app.services.auth.requests.post")
    def test_login_success(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "access-123",
            "refresh_token": "refresh-456",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = auth_service.login(username="user", password="pass")

        assert isinstance(result, AuthResponse)
        assert result.access_token == "access-123"
        assert result.refresh_token == "refresh-456"
        mock_post.assert_called_once_with(
            url=auth_service.token_url,
            data={
                "grant_type": "password",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "username": "user",
                "password": "pass",
                "scope": "offline_access",
            },
        )

    @patch("app.services.auth.requests.post")
    def test_login_missing_access_token(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "refresh_token": "refresh-456",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.login(username="user", password="pass")

    @patch("app.services.auth.requests.post")
    def test_login_missing_refresh_token(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "access-123",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.login(username="user", password="pass")

    @patch("app.services.auth.requests.post")
    def test_login_request_exception(self, mock_post, auth_service):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service.login(username="user", password="pass")

    @patch("app.services.auth.requests.post")
    def test_login_http_error(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Unauthorized"
        )
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.login(username="user", password="wrong")

    @patch("app.services.auth.requests.post")
    def test_renew_success(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-access-123",
            "refresh_token": "new-refresh-456",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = auth_service.renew(refresh_token="old-refresh")

        assert isinstance(result, AuthResponse)
        assert result.access_token == "new-access-123"
        assert result.refresh_token == "new-refresh-456"
        mock_post.assert_called_once_with(
            url=auth_service.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "refresh_token": "old-refresh",
            },
        )

    @patch("app.services.auth.requests.post")
    def test_renew_missing_access_token(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.renew(refresh_token="old-refresh")

    @patch("app.services.auth.requests.post")
    def test_renew_request_exception(self, mock_post, auth_service):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service.renew(refresh_token="old-refresh")
