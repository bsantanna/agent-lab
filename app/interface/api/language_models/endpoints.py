from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Response, status

from app.application.services.language_models import (
    LanguageModelService,
    LanguageModelSettingService,
)
from app.core.container import Container
from app.domain.exceptions.base import NotFoundError
from app.domain.models import LanguageModel
from app.interface.api.language_models.schema import (
    LanguageModelCreateRequest,
    LanguageModelResponse,
    LanguageModelSettingResponse,
    LanguageModelExpandedResponse,
    LanguageModelUpdateRequest,
    LanguageModelSettingUpdateRequest,
)

router = APIRouter()


@router.get("/list", response_model=List[LanguageModelResponse])
@inject
def get_list(
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    language_models = language_model_service.get_language_models()
    return [LanguageModelResponse.model_validate(lm) for lm in language_models]


@router.get("/{language_model_id}", response_model=LanguageModelExpandedResponse)
@inject
def get_by_id(
    language_model_id: str,
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
):
    try:
        language_model = language_model_service.get_language_model_by_id(
            language_model_id
        )

        return _format_expanded_response(language_model, language_model_setting_service)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=LanguageModelResponse
)
@inject
def add(
    language_model_data: LanguageModelCreateRequest = Body(...),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    language_model = language_model_service.create_language_model(
        integration_id=language_model_data.integration_id,
        language_model_tag=language_model_data.language_model_tag,
    )
    return LanguageModelResponse.model_validate(language_model)


@router.delete("/delete/{language_model_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def remove(
    language_model_id: str,
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


@router.post(path="/update", response_model=LanguageModelResponse)
@inject
def update_tag(
    language_model_data: LanguageModelUpdateRequest = Body(...),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
):
    try:
        language_model = language_model_service.update_language_model(
            language_model_id=language_model_data.language_model_id,
            language_model_tag=language_model_data.language_model_tag,
        )
        return LanguageModelResponse.model_validate(language_model)
    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(path="/update_setting", response_model=LanguageModelExpandedResponse)
@inject
def update_setting(
    language_model_data: LanguageModelSettingUpdateRequest = Body(...),
    language_model_service: LanguageModelService = Depends(
        Provide[Container.language_model_service]
    ),
    language_model_setting_service: LanguageModelSettingService = Depends(
        Provide[Container.language_model_setting_service]
    ),
):
    try:
        language_model_setting_service.update_by_key(
            language_model_id=language_model_data.language_model_id,
            setting_key=language_model_data.setting_key,
            setting_value=language_model_data.setting_value,
        )

        language_model = language_model_service.get_language_model_by_id(
            language_model_id=language_model_data.language_model_id
        )

        return _format_expanded_response(language_model, language_model_setting_service)

    except NotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


def _format_expanded_response(
    language_model: LanguageModel,
    language_model_setting_service: LanguageModelSettingService,
):
    settings = language_model_setting_service.get_language_model_settings(
        language_model.id
    )
    response = LanguageModelExpandedResponse.model_validate(language_model)
    response.lm_settings = [
        LanguageModelSettingResponse.model_validate(setting) for setting in settings
    ]
    return response
