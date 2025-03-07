from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, File, Depends
from starlette import status

from app.core.container import Container
from app.interface.api.attachments.schema import AttachmentResponse
from app.services.attachments import AttachmentService

router = APIRouter()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
)
@inject
async def upload_attachment(
    file=File(...),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    attachment = await attachment_service.create_attachment(file=file)

    return AttachmentResponse.model_validate(attachment)
