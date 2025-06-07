from io import BytesIO

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, File, Depends, Body, Path
from starlette import status
from starlette.responses import StreamingResponse

from app.core.container import Container
from app.interface.api.attachments.schema import Attachment, EmbeddingsRequest
from app.services.attachments import AttachmentService

router = APIRouter()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=Attachment,
    summary="Upload a file attachment",
    description="""
    Upload a file attachment to the system.

    This endpoint accepts any file type and stores it in the system for later use.
    The file is processed and metadata is extracted and stored along with the file content.

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
                "application/json": {"example": {"detail": "File size too large"}}
            },
        },
        422: {
            "description": "Validation error",
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
):
    """
    Upload a file attachment to the system.

    This endpoint processes the uploaded file, extracts metadata,
    and stores it securely in the system for later retrieval.
    """
    attachment = await attachment_service.create_attachment_with_file(file=file)
    return Attachment.model_validate(attachment)


@router.get(
    "/download/{attachment_id}",
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
        403: {
            "description": "Access forbidden - insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You don't have permission to access this attachment"
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
):
    """
    Download an attachment by its unique identifier.

    Returns the file content as a streaming response with appropriate
    headers for file download.
    """
    attachment = attachment_service.get_attachment_by_id(attachment_id)
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
        400: {
            "description": "Bad request - Invalid parameters or unsupported file type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File type not supported for embedding generation"
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
        500: {
            "description": "Internal server error - Embedding generation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to generate embeddings due to service error"
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
):
    """
    Generate vector embeddings for an attachment.

    This endpoint processes the attachment content and generates
    vector embeddings using the specified language model.
    """
    attachment = await attachment_service.create_embeddings(
        attachment_id=embeddings.attachment_id,
        language_model_id=embeddings.language_model_id,
        collection_name=embeddings.collection_name,
    )
    return Attachment.model_validate(attachment)
