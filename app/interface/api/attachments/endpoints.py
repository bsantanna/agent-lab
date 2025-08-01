from io import BytesIO

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, File, Depends, Body, Path
from fastapi.security import HTTPBearer
from fastapi_keycloak_middleware import get_user
from starlette import status
from starlette.responses import StreamingResponse

from app.core.container import Container
from app.domain.exceptions.base import FileToLargeError
from app.infrastructure.auth.schema import User
from app.interface.api.attachments.schema import Attachment, EmbeddingsRequest
from app.services.attachments import AttachmentService

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post(
    "/upload",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_201_CREATED,
    response_model=Attachment,
    summary="Upload a file attachment",
    description="""
    Upload a file attachment to the system.

    This endpoint accepts any file type and stores it in the system for later use.
    The file is processed and metadata is extracted and stored along with the file content.

    **Upload size limit is set to 10 MB per file.**

    **Example file types:**
    - Documents (PDF, DOC, DOCX, TXT)
    - Images (JPG, PNG, GIF, BMP)
    - Archives (ZIP, RAR, TAR)

    """,
    response_description="Successfully uploaded attachment with metadata",
    responses={
        201: {
            "description": "Attachment successfully uploaded",
            "content": {
                "application/json": {
                    "example": {
                        "id": "att_123456789",
                        "is_active": True,
                        "file_name": "document.pdf",
                        "created_at": "2024-01-15T10:30:00Z",
                        "parsed_content": "Extracted text content from the document",
                    }
                }
            },
        },
        413: {
            "description": "Payload too large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File size 1234 exceeds the maximum allowed size of 123 bytes"
                    }
                }
            },
        },
        422: {
            "description": "Validation or file processing error",
            "content": {
                "application/json": {"example": {"detail": "No file provided"}}
            },
        },
    },
)
@inject
async def upload_attachment(
    file=File(..., description="The file to upload.", example="document.pdf"),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
    user: User = Depends(get_user),
):
    """
    Upload a file attachment to the system.

    This endpoint processes the uploaded file, extracts metadata,
    and stores it securely in the system for later retrieval.
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    # validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    max_size = 10 * 1024 * 1024  # 10 MB
    if file_size > max_size:
        raise FileToLargeError(file_size, max_size)
    file.file.seek(0)

    attachment = await attachment_service.create_attachment_with_file(
        file=file, schema=schema
    )
    return Attachment.model_validate(attachment)


@router.get(
    "/download/{attachment_id}",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    summary="Download an attachment by ID",
    description="""
    Download a previously uploaded attachment by its unique identifier.

    This endpoint streams the file content directly to the client with appropriate
    headers for file download. The original filename and content type are preserved.

    **Usage:**
    - Use the attachment ID obtained from the upload endpoint
    - The file will be downloaded with its original filename
    - Content-Type header will match the original file type
    """,
    response_description="File content streamed as attachment",
    responses={
        200: {
            "description": "File successfully downloaded",
            "content": {"application/octet-stream": {"example": "Binary file content"}},
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename",
                    "schema": {
                        "type": "string",
                        "example": "attachment; filename=document.pdf",
                    },
                }
            },
        },
        404: {
            "description": "Attachment not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Attachment with ID 'att_123456789' not found"
                    }
                }
            },
        },
    },
)
@inject
async def download_attachment(
    attachment_id: str = Path(
        ...,
        description="Unique identifier of the attachment to download",
        example="att_123456789",
        min_length=1,
        max_length=50,
    ),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
    user: User = Depends(get_user),
):
    """
    Download an attachment by its unique identifier.

    Returns the file content as a streaming response with appropriate
    headers for file download.
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    attachment = attachment_service.get_attachment_by_id(attachment_id, schema)
    response = StreamingResponse(
        BytesIO(attachment.raw_content),
        media_type="application/octet-stream",
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename={attachment.file_name}"
    )
    return response


@router.post(
    "/embeddings",
    dependencies=[Depends(bearer_scheme)],
    status_code=status.HTTP_201_CREATED,
    response_model=Attachment,
    summary="Generate embeddings for an attachment",
    description="""
    Generate vector embeddings for a previously uploaded attachment.

    This endpoint processes the content of an attachment and generates vector embeddings
    using the specified language model. These embeddings can be used for:

    - **Semantic search**: Find similar content based on meaning
    - **Content analysis**: Analyze document themes and topics
    - **Recommendation systems**: Suggest related documents
    - **Classification**: Categorize content automatically

    **Process:**
    1. Extract text content from the attachment
    2. Process text using the specified language model
    3. Generate vector embeddings
    4. Store embeddings in the specified collection

    **Supported file types for embedding generation:**
    - Text documents (TXT, MD, RTF)
    - PDF documents
    - Word documents (DOC, DOCX)
    - HTML files
    - CSV files
    - JSON files
    - Images (JPG, PNG)
    - Audio files (WAV, MP3, OGG, WEBM)
    """,
    response_description="Attachment updated with embedding information",
    responses={
        201: {
            "description": "Embeddings successfully generated",
            "content": {
                "application/json": {
                    "example": {
                        "id": "att_123456789",
                        "is_active": True,
                        "file_name": "document.pdf",
                        "created_at": "2024-01-15T10:30:00Z",
                        "parsed_content": "Extracted text content from the document",
                        "embeddings_collection": "my_documents",
                    }
                }
            },
        },
        404: {
            "description": "Attachment or language model not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Attachment with ID 'att_123456789' not found"
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid language model ID or collection name"
                    }
                }
            },
        },
    },
)
@inject
async def create_embeddings(
    embeddings: EmbeddingsRequest = Body(
        ...,
        description="Configuration for embedding generation",
        example={
            "attachment_id": "att_123456789",
            "language_model_id": "llm_id_987654321",
            "collection_name": "my_documents",
        },
    ),
    attachment_service: AttachmentService = Depends(
        Provide[Container.attachment_service]
    ),
    user: User = Depends(get_user),
):
    """
    Generate vector embeddings for an attachment.

    This endpoint processes the attachment content and generates
    vector embeddings using the specified language model.
    """
    schema = user.id.replace("-", "_") if user is not None else "public"
    attachment = await attachment_service.create_embeddings(
        attachment_id=embeddings.attachment_id,
        language_model_id=embeddings.language_model_id,
        collection_name=embeddings.collection_name,
        schema=schema,
    )
    return Attachment.model_validate(attachment)
