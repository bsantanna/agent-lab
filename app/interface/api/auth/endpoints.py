from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, status, Body, Depends

from app.core.container import Container
from app.interface.api.auth.schema import AuthResponse, LoginRequest, RenewRequest
from app.services.auth import AuthService

router = APIRouter()


@router.post(
    path="/login",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
    summary="Authenticate and obtain a bearer token",
    description="""
    Authenticates a user with username and password, and returns an access token
    and a refresh token. Use the access token in the `Authorization: Bearer <token>`
    header for subsequent authenticated requests.

    Parameters (JSON body):
    - `username`: The user's login name.
    - `password`: The user's password.
    """,
    response_description="Access and refresh tokens",
    responses={
        201: {
            "description": "Token successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials provided. Please check your username and password."}
                }
            },
        },
        422: {
            "description": "Validation error",
        },
    },
)
@inject
async def login(
    login_data: LoginRequest = Body(...),
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
):
    return auth_service.login(
        username=login_data.username, password=login_data.password
    )


@router.post(
    path="/renew",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
    summary="Renew a bearer token",
    description="""
    Obtains a new access token using an existing refresh token, without requiring
    the user to log in again.

    Parameters (JSON body):
    - `refresh_token`: A valid refresh token obtained from the login endpoint.
    """,
    response_description="New access and refresh tokens",
    responses={
        201: {
            "description": "Token successfully renewed",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                    }
                }
            },
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid credentials provided."}
                }
            },
        },
    },
)
@inject
async def renew(
    renew_request: RenewRequest = Body(...),
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
):
    return auth_service.renew(renew_request.refresh_token)
