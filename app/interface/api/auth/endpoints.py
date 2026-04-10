from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, status, Body, Depends
from fastapi_keycloak_middleware import get_user
from typing_extensions import Annotated

from app.core.container import Container
from app.infrastructure.auth.schema import User
from app.interface.api.auth.schema import (
    AuthResponse,
    ExchangeRequest,
    LoginRequest,
    RenewRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
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
                    "example": {
                        "detail": "Invalid credentials provided. Please check your username and password."
                    }
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
    login_data: Annotated[LoginRequest, Body(...)],
    auth_service: Annotated[AuthService, Depends(Provide[Container.auth_service])],
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
    renew_request: Annotated[RenewRequest, Body(...)],
    auth_service: Annotated[AuthService, Depends(Provide[Container.auth_service])],
):
    return auth_service.renew(renew_request.refresh_token)


@router.post(
    path="/exchange",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthResponse,
    summary="Exchange an authorization code for tokens (PKCE)",
    description="""
    Exchanges an authorization code obtained from the Keycloak login page for
    access and refresh tokens. Used by the Authorization Code + PKCE flow.

    Parameters (JSON body):
    - `code`: The authorization code from Keycloak's redirect.
    - `code_verifier`: The PKCE code verifier that matches the code challenge sent during login.
    - `redirect_uri`: The redirect URI used in the authorization request.
    """,
    response_description="Access and refresh tokens",
    responses={
        201: {
            "description": "Tokens successfully obtained",
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
            "description": "Invalid authorization code or code verifier",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Authentication failed: invalid authorization code"
                    }
                }
            },
        },
    },
)
@inject
async def exchange(
    exchange_request: Annotated[ExchangeRequest, Body(...)],
    auth_service: Annotated[AuthService, Depends(Provide[Container.auth_service])],
):
    return auth_service.exchange(
        code=exchange_request.code,
        code_verifier=exchange_request.code_verifier,
        redirect_uri=exchange_request.redirect_uri,
    )


@router.get(
    path="/profile",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile from Keycloak.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
@inject
async def get_profile(
    user: Annotated[User, Depends(get_user)],
    auth_service: Annotated[AuthService, Depends(Provide[Container.auth_service])],
):
    return auth_service.get_user_profile(user_id=user.id)


@router.put(
    path="/profile",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileResponse,
    summary="Update current user profile",
    description="Updates the authenticated user's profile in Keycloak.",
    responses={
        200: {"description": "User profile updated successfully"},
        401: {"description": "Not authenticated"},
        409: {"description": "Email or username already in use"},
    },
)
@inject
async def update_profile(
    profile_data: Annotated[UserProfileUpdateRequest, Body(...)],
    user: Annotated[User, Depends(get_user)],
    auth_service: Annotated[AuthService, Depends(Provide[Container.auth_service])],
):
    return auth_service.update_user_profile(
        user_id=user.id,
        username=profile_data.username,
        email=profile_data.email,
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
    )
