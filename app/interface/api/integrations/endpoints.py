from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from app.application.services.integrations import IntegrationService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError

router = APIRouter()


@router.get("/list")
@inject
def get_list(
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    return integration_service.get_integrations()


@router.get("/{integration_id}")
@inject
def get_by_id(
    integration_id: int,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    try:
        return integration_service.get_integration_by_id(integration_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/create", status_code=status.HTTP_201_CREATED)
@inject
def add(
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    return integration_service.create_integration()


@router.delete("/delete/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def remove(
    integration_id: int,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    try:
        integration_service.delete_integration_by_id(integration_id)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
