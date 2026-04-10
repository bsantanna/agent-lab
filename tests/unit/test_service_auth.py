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

    # -- exchange --

    @patch("app.services.auth.requests.post")
    def test_exchange_success(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "access-abc",
            "refresh_token": "refresh-def",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = auth_service.exchange(
            code="auth-code", code_verifier="verifier", redirect_uri="http://localhost/cb"
        )

        assert isinstance(result, AuthResponse)
        assert result.access_token == "access-abc"
        assert result.refresh_token == "refresh-def"
        mock_post.assert_called_once_with(
            url=auth_service.token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "code": "auth-code",
                "code_verifier": "verifier",
                "redirect_uri": "http://localhost/cb",
            },
        )

    @patch("app.services.auth.requests.post")
    def test_exchange_missing_access_token(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"refresh_token": "refresh-def"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.exchange(
                code="auth-code", code_verifier="verifier", redirect_uri="http://localhost/cb"
            )

    @patch("app.services.auth.requests.post")
    def test_exchange_missing_refresh_token(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "access-abc"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.exchange(
                code="auth-code", code_verifier="verifier", redirect_uri="http://localhost/cb"
            )

    @patch("app.services.auth.requests.post")
    def test_exchange_request_exception(self, mock_post, auth_service):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service.exchange(
                code="auth-code", code_verifier="verifier", redirect_uri="http://localhost/cb"
            )

    @patch("app.services.auth.requests.post")
    def test_exchange_http_error(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "400 Bad Request"
        )
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.exchange(
                code="bad-code", code_verifier="verifier", redirect_uri="http://localhost/cb"
            )

    # -- _get_service_account_token --

    @patch("app.services.auth.requests.post")
    def test_get_service_account_token_success(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "sa-token-123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = auth_service._get_service_account_token()

        assert result == "sa-token-123"
        mock_post.assert_called_once_with(
            url=auth_service.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )

    @patch("app.services.auth.requests.post")
    def test_get_service_account_token_missing(self, mock_post, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service._get_service_account_token()

    @patch("app.services.auth.requests.post")
    def test_get_service_account_token_request_exception(self, mock_post, auth_service):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service._get_service_account_token()

    # -- get_user_profile --

    @patch("app.services.auth.requests.get")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_get_user_profile_success(self, mock_sa_token, mock_get, auth_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = auth_service.get_user_profile(user_id="id_abc-def-123")

        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        mock_get.assert_called_once_with(
            url=f"{auth_service.admin_users_url}/abc-def-123",
            headers={"Authorization": "Bearer sa-token"},
        )

    @patch("app.services.auth.requests.get")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_get_user_profile_request_exception(self, mock_sa_token, mock_get, auth_service):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service.get_user_profile(user_id="id_abc-def-123")

    @patch("app.services.auth.requests.get")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_get_user_profile_http_error(self, mock_sa_token, mock_get, auth_service):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.get_user_profile(user_id="id_abc-def-123")

    # -- update_user_profile --

    @patch("app.services.auth.requests.put")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_update_user_profile_success(self, mock_sa_token, mock_put, auth_service):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        result = auth_service.update_user_profile(
            user_id="id_abc-def-123",
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="Name",
        )

        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.first_name == "New"
        assert result.last_name == "Name"
        mock_put.assert_called_once_with(
            url=f"{auth_service.admin_users_url}/abc-def-123",
            headers={
                "Authorization": "Bearer sa-token",
                "Content-Type": "application/json",
            },
            json={
                "username": "newuser",
                "email": "new@example.com",
                "firstName": "New",
                "lastName": "Name",
            },
        )

    @patch("app.services.auth.requests.put")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_update_user_profile_conflict_409(self, mock_sa_token, mock_put, auth_service):
        mock_response = MagicMock()
        mock_response.status_code = 409
        http_error = requests.exceptions.HTTPError("409 Conflict")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_put.return_value = mock_response

        with pytest.raises(AuthenticationError, match="409"):
            auth_service.update_user_profile(
                user_id="id_abc-def-123",
                username="taken",
                email="taken@example.com",
                first_name="A",
                last_name="B",
            )

    @patch("app.services.auth.requests.put")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_update_user_profile_http_error_non_409(self, mock_sa_token, mock_put, auth_service):
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_put.return_value = mock_response

        with pytest.raises(AuthenticationError):
            auth_service.update_user_profile(
                user_id="id_abc-def-123",
                username="user",
                email="u@example.com",
                first_name="A",
                last_name="B",
            )

    @patch("app.services.auth.requests.put")
    @patch.object(AuthService, "_get_service_account_token", return_value="sa-token")
    def test_update_user_profile_request_exception(self, mock_sa_token, mock_put, auth_service):
        mock_put.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(AuthenticationError):
            auth_service.update_user_profile(
                user_id="id_abc-def-123",
                username="user",
                email="u@example.com",
                first_name="A",
                last_name="B",
            )

    # -- init admin_users_url --

    def test_admin_users_url(self, auth_service):
        assert (
            auth_service.admin_users_url
            == "http://keycloak:8080/admin/realms/test-realm/users"
        )
