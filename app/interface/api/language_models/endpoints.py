from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from app.application.services.language_models import LanguageModelService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError

router = APIRouter()


@router.get("/list")
@inject
def get_list(
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    return language_model_service.get_language_models()


@router.get("/{language_model_id}")
@inject
def get_by_id(
    language_model_id: int,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    try:
        return language_model_service.get_language_model_by_id(language_model_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/create", status_code=status.HTTP_201_CREATED)
@inject
def add(
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    return language_model_service.create_language_model()


@router.delete("/delete/{language_model_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def remove(
    language_model_id: int,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    try:
        language_model_service.delete_language_model_by_id(language_model_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
