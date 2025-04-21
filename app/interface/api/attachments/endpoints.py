from io import BytesIO

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, File, Depends, Body
from starlette import status
from starlette.responses import StreamingResponse

from app.core.container import Container
from app.interface.api.attachments.schema import AttachmentResponse, EmbeddingsRequest
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
    attachment = await attachment_service.create_attachment_with_file(file=file)

    return AttachmentResponse.model_validate(attachment)


@router.get(
    "/download/{attachment_id}",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
)
@inject
async def download_attachment(
    attachment_id: str,
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    attachment = attachment_service.get_attachment_by_id(attachment_id)
    response = StreamingResponse(
        BytesIO(attachment.raw_content), media_type="application/octet-stream"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename={attachment.file_name}"
    )
    return response


@router.post(
    "/embeddings",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
)
@inject
async def create_embeddings(
    embeddings: EmbeddingsRequest = Body(...),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
):
    attachment = await attachment_service.create_embeddings(
        attachment_id=embeddings.attachment_id,
        language_model_id=embeddings.language_model_id,
        collection_name=embeddings.collection_name,
    )

    return AttachmentResponse.model_validate(attachment)
