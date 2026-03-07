from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_upload_storage
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.uploads import UploadPresignRead, UploadPresignRequest
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
