from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status, Body

from app.application.services.integrations import IntegrationService
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.interface.api.integrations.schema import IntegrationCreateRequest

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
    integration_data: IntegrationCreateRequest = Body(...),
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    return integration_service.create_integration(
        integration_type=integration_data.integration_type,
        api_endpoint=integration_data.api_endpoint,
        api_key=integration_data.api_key,
    )


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
