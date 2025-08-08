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
    summary="Create a new bearer token",
    description="Create a new bearer token for the user. This endpoint is used to authenticate users and provide them with a token that can be used for subsequent requests.",
    response_description="Successfully created bearer token",
    responses={
        201: {
            "description": "Token successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "a_valid_token_string",
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
            "description": "Invalid data unprocessable entity",
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
    summary="Renew an existing bearer token",
    description="Renew an existing bearer token using a refresh token. This endpoint is used to obtain a new access token without requiring the user to log in again.",
    response_description="Successfully renewed bearer token",
    responses={
        201: {
            "description": "Token successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "a_valid_token_string",
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
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
