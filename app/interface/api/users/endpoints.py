from fastapi import APIRouter, Depends, Response, status
from dependency_injector.wiring import inject, Provide

from app.application.services.user import UserService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError


router = APIRouter()


@router.get("/list")
@inject
def get_list(
        user_service: UserService = Depends(Provide[Container.user_service]),
):
    return user_service.get_users()


@router.get("/{user_id}")
@inject
def get_by_id(
        user_id: int,
        user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        return user_service.get_user_by_id(user_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/create", status_code=status.HTTP_201_CREATED)
@inject
def add(
        user_service: UserService = Depends(Provide[Container.user_service]),
):
    return user_service.create_user()


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def remove(
        user_id: int,
        user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        user_service.delete_user_by_id(user_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

