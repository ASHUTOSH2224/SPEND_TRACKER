from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session, get_upload_storage
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.statements import (
    StatementCreate,
    StatementDeleteResult,
    StatementListQuery,
    StatementRead,
    StatementUploadStatus,
)
from app.services.statements import (
    create_statement_for_user,
    delete_statement_for_user,
    get_statement_for_user,
    list_statements_for_user,
    retry_statement_for_user,
)
from app.services.storage import UploadStorage

router = APIRouter(prefix="/statements", tags=["statements"])


def _serialize_statement(statement) -> StatementRead:
    return StatementRead.model_validate(statement)


def get_statement_list_query(
    card_id: UUID | None = None,
    status: StatementUploadStatus | None = None,
    month: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> StatementListQuery:
    try:
        return StatementListQuery(
            card_id=card_id,
            status=status,
            month=month,
            page=page,
            page_size=page_size,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.post(
    "",
    response_model=ResponseEnvelope[StatementRead],
    status_code=status.HTTP_201_CREATED,
)
def create_statement(
    payload: StatementCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    storage: UploadStorage = Depends(get_upload_storage),
) -> ResponseEnvelope[StatementRead]:
    statement = create_statement_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
        storage=storage,
    )
    return success_response(_serialize_statement(statement))


@router.get(
    "",
    response_model=ResponseEnvelope[list[StatementRead]],
    status_code=status.HTTP_200_OK,
)
def list_statements(
    filters: StatementListQuery = Depends(get_statement_list_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[StatementRead]]:
    statements, meta = list_statements_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response([_serialize_statement(statement) for statement in statements], meta=meta)


@router.get(
    "/{statement_id}",
    response_model=ResponseEnvelope[StatementRead],
    status_code=status.HTTP_200_OK,
)
def get_statement(
    statement_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[StatementRead]:
    statement = get_statement_for_user(
        session,
        user_id=current_user.id,
        statement_id=statement_id,
    )
    return success_response(_serialize_statement(statement))


@router.post(
    "/{statement_id}/retry",
    response_model=ResponseEnvelope[StatementRead],
    status_code=status.HTTP_200_OK,
)
def retry_statement(
    statement_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[StatementRead]:
    statement = retry_statement_for_user(
        session,
        user_id=current_user.id,
        statement_id=statement_id,
    )
    return success_response(_serialize_statement(statement))


@router.delete(
    "/{statement_id}",
    response_model=ResponseEnvelope[StatementDeleteResult],
    status_code=status.HTTP_200_OK,
)
def delete_statement(
    statement_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    storage: UploadStorage = Depends(get_upload_storage),
) -> ResponseEnvelope[StatementDeleteResult]:
    result = delete_statement_for_user(
        session,
        user_id=current_user.id,
        statement_id=statement_id,
        storage=storage,
    )
    return success_response(result)
