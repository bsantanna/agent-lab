import requests

from app.domain.exceptions.base import AuthenticationError
from app.interface.api.auth.schema import AuthResponse, UserProfileResponse


_TOKEN_NOT_FOUND = "Access token or refresh token not found in response"


class AuthService:
    def __init__(
        self,
        enabled: bool,
        url: str,
        realm: str,
        client_id: str,
        client_secret: str,
    ):
        self.enabled = enabled
        self.url = url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = f"{self.url}/realms/{self.realm}/protocol/openid-connect/token"
        self.admin_users_url = f"{self.url}/admin/realms/{self.realm}/users"

    def login(self, username: str, password: str) -> AuthResponse:
        try:
            response = requests.post(
                url=self.token_url,
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": username,
                    "password": password,
                    "scope": "offline_access",
                },
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            if not access_token or not refresh_token:
                raise AuthenticationError(_TOKEN_NOT_FOUND)
            return AuthResponse(access_token=access_token, refresh_token=refresh_token)
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    def exchange(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> AuthResponse:
        try:
            response = requests.post(
                url=self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "code_verifier": code_verifier,
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            if not access_token or not refresh_token:
                raise AuthenticationError(_TOKEN_NOT_FOUND)
            return AuthResponse(
                access_token=access_token, refresh_token=refresh_token
            )
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    def renew(self, refresh_token: str) -> AuthResponse:
        try:
            response = requests.post(
                url=self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            if not new_access_token or not new_refresh_token:
                raise AuthenticationError(_TOKEN_NOT_FOUND)
            return AuthResponse(
                access_token=new_access_token, refresh_token=new_refresh_token
            )
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    def _get_service_account_token(self) -> str:
        try:
            response = requests.post(
                url=self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise AuthenticationError(
                    "Service account token not found in response"
                )
            return token
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    def get_user_profile(self, user_id: str) -> UserProfileResponse:
        raw_uuid = user_id.removeprefix("id_")
        token = self._get_service_account_token()
        try:
            response = requests.get(
                url=f"{self.admin_users_url}/{raw_uuid}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            return UserProfileResponse(
                username=data.get("username", ""),
                email=data.get("email", ""),
                first_name=data.get("firstName", ""),
                last_name=data.get("lastName", ""),
            )
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    def update_user_profile(
        self,
        user_id: str,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> UserProfileResponse:
        raw_uuid = user_id.removeprefix("id_")
        token = self._get_service_account_token()
        try:
            response = requests.put(
                url=f"{self.admin_users_url}/{raw_uuid}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "username": username,
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                },
            )
            response.raise_for_status()
            return UserProfileResponse(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                raise AuthenticationError(
                    "409: A user with this email or username already exists"
                )
            raise AuthenticationError(str(exc))
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))
