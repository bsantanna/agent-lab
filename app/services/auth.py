import requests

from app.domain.exceptions.base import AuthenticationError
from app.interface.api.auth.schema import AuthResponse


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

    async def login(self, username: str, password: str) -> AuthResponse:
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
                raise AuthenticationError(
                    "Access token or refresh token not found in response"
                )
            return AuthResponse(access_token=access_token, refresh_token=refresh_token)
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))

    async def renew(self, refresh_token: str) -> AuthResponse:
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
            if not new_access_token:
                raise AuthenticationError("Access token not found in response")
            return AuthResponse(
                access_token=new_access_token, refresh_token=new_refresh_token
            )
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(str(exc))
