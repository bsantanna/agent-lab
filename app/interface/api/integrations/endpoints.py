from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status
from typing_extensions import List

from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.interface.api.integrations.schema import (
    IntegrationCreateRequest,
    IntegrationResponse,
)
from app.services.integrations import IntegrationService

router = APIRouter()


@router.get(path="/list", response_model=List[IntegrationResponse])
@inject
async def get_list(
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    integrations = integration_service.get_integrations()
    return [
        IntegrationResponse.model_validate(integration) for integration in integrations
    ]


@router.get(path="/{integration_id}", response_model=IntegrationResponse)
@inject
async def get_by_id(
    integration_id: str,
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    try:
        integration = integration_service.get_integration_by_id(integration_id)
        return IntegrationResponse.model_validate(integration)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=IntegrationResponse
)
@inject
async def add(
    integration_data: IntegrationCreateRequest = Body(...),
    integration_service: IntegrationService = Depends(
        Provide[Container.integration_service]
    ),
):
    integration = integration_service.create_integration(
        integration_type=integration_data.integration_type,
        api_endpoint=integration_data.api_endpoint,
        api_key=integration_data.api_key,
    )

    return IntegrationResponse.model_validate(integration)


@router.delete("/delete/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def remove(
    integration_id: str,
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
