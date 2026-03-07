from fastapi import APIRouter, Body, Depends, Query, status

from app.api.deps import get_current_user, get_upload_storage
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.uploads import (
    UploadPresignRead,
    UploadPresignRequest,
    UploadStoreRead,
)
from app.services.storage import UploadStorage

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/presign",
    response_model=ResponseEnvelope[UploadPresignRead],
    status_code=status.HTTP_200_OK,
)
def presign_upload(
    payload: UploadPresignRequest,
    current_user: User = Depends(get_current_user),
    storage: UploadStorage = Depends(get_upload_storage),
) -> ResponseEnvelope[UploadPresignRead]:
    upload_target = storage.create_upload_target(
        user_id=current_user.id,
        file_name=payload.file_name,
        content_type=payload.content_type,
    )
    return success_response(
        UploadPresignRead(
            upload_url=upload_target.upload_url,
            file_storage_key=upload_target.file_storage_key,
        )
    )


@router.put(
    "/content",
    response_model=ResponseEnvelope[UploadStoreRead],
    status_code=status.HTTP_200_OK,
)
def upload_statement_content(
    file_storage_key: str = Query(min_length=1, max_length=1024),
    content: bytes = Body(),
    current_user: User = Depends(get_current_user),
    storage: UploadStorage = Depends(get_upload_storage),
) -> ResponseEnvelope[UploadStoreRead]:
    if not storage.is_owned_key(
        user_id=current_user.id,
        file_storage_key=file_storage_key,
    ):
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="INVALID_FILE_STORAGE_KEY",
            message="file_storage_key must belong to the authenticated user",
        )

    storage.store_object(
        file_storage_key=file_storage_key,
        content=content,
    )
    return success_response(
        UploadStoreRead(
            stored=True,
            file_storage_key=file_storage_key,
        )
    )
