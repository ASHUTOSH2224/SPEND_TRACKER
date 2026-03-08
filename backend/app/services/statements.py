from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.secrets import seal_secret
from app.core.exceptions import AppException
from app.models.card import Card
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas.statements import StatementCreate, StatementDeleteResult, StatementListQuery
from app.services.charge_summaries import (
    get_statement_charge_summary_periods,
    refresh_card_charge_summaries_for_periods,
)
from app.services.statement_jobs import (
    delete_statement_processing_jobs_for_statement,
    enqueue_statement_processing_job,
)
from app.services.storage import UploadStorage


def create_statement_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: StatementCreate,
    storage: UploadStorage,
    statement_secret_key: str,
) -> Statement:
    card = _get_card_for_statement_create(session, user_id=user_id, card_id=payload.card_id)
    if not storage.is_owned_key(
        user_id=user_id,
        file_storage_key=payload.file_storage_key,
    ):
        raise AppException(
            status_code=422,
            code="INVALID_FILE_STORAGE_KEY",
            message="file_storage_key must belong to the authenticated user",
        )

    statement = Statement(
        user_id=user_id,
        card_id=card.id,
        file_name=payload.file_name,
        file_storage_key=payload.file_storage_key,
        file_password_encrypted=(
            seal_secret(payload.file_password, secret_key=statement_secret_key)
            if payload.file_password is not None
            else None
        ),
        file_type=payload.file_type,
        statement_period_start=payload.statement_period_start,
        statement_period_end=payload.statement_period_end,
        upload_status="uploaded",
        extraction_status="pending",
        categorization_status="pending",
        transaction_count=0,
        processing_error=None,
    )
    session.add(statement)
    session.commit()
    session.refresh(statement)
    enqueue_statement_processing_job(
        session,
        statement_id=statement.id,
        trigger_source="create",
    )
    return statement


def list_statements_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: StatementListQuery,
) -> tuple[list[Statement], dict[str, int]]:
    statement = select(Statement).where(Statement.user_id == user_id)

    if filters.card_id is not None:
        statement = statement.where(Statement.card_id == filters.card_id)
    if filters.status is not None:
        statement = statement.where(Statement.upload_status == filters.status)

    month_bounds = filters.month_bounds()
    if month_bounds is not None:
        month_start, month_end = month_bounds
        statement = statement.where(
            Statement.statement_period_start <= month_end,
            Statement.statement_period_end >= month_start,
        )

    total = session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    ) or 0

    offset = (filters.page - 1) * filters.page_size
    paginated_statement = statement.order_by(
        Statement.statement_period_end.desc(),
        Statement.uploaded_at.desc(),
        Statement.created_at.desc(),
    ).offset(offset).limit(filters.page_size)

    statements = list(session.scalars(paginated_statement).all())
    meta = {
        "page": filters.page,
        "page_size": filters.page_size,
        "total": total,
        "total_pages": ceil(total / filters.page_size) if total else 0,
    }
    return statements, meta


def get_statement_for_user(
    session: Session,
    *,
    user_id: UUID,
    statement_id: UUID,
) -> Statement:
    statement = session.scalar(
        select(Statement).where(
            Statement.id == statement_id,
            Statement.user_id == user_id,
        )
    )
    if statement is None:
        raise AppException(
            status_code=404,
            code="STATEMENT_NOT_FOUND",
            message="Statement not found",
        )
    return statement


def retry_statement_for_user(
    session: Session,
    *,
    user_id: UUID,
    statement_id: UUID,
) -> Statement:
    statement = get_statement_for_user(session, user_id=user_id, statement_id=statement_id)
    if not _statement_can_retry(statement):
        raise AppException(
            status_code=409,
            code="STATEMENT_RETRY_NOT_ALLOWED",
            message="Only failed statements can be retried",
        )

    statement.upload_status = "uploaded"
    statement.extraction_status = "pending"
    statement.categorization_status = "pending"
    statement.transaction_count = 0
    statement.processing_error = None

    session.commit()
    session.refresh(statement)
    enqueue_statement_processing_job(
        session,
        statement_id=statement.id,
        trigger_source="retry",
    )
    return statement


def delete_statement_for_user(
    session: Session,
    *,
    user_id: UUID,
    statement_id: UUID,
    storage: UploadStorage,
) -> StatementDeleteResult:
    statement = get_statement_for_user(session, user_id=user_id, statement_id=statement_id)
    charge_summary_periods = get_statement_charge_summary_periods(
        session,
        statement=statement,
    )
    transaction_count = session.scalar(
        select(func.count()).where(Transaction.statement_id == statement.id)
    ) or 0
    if transaction_count:
        raise AppException(
            status_code=409,
            code="STATEMENT_DELETE_NOT_ALLOWED",
            message="Statements with imported transactions cannot be deleted",
        )

    storage_deleted = storage.delete_object(file_storage_key=statement.file_storage_key)

    result = StatementDeleteResult(
        id=statement.id,
        deleted=True,
        transactions_deleted=0,
        storage_object_deleted=storage_deleted,
        delete_policy=(
            "Deletes the statement metadata row and any queued processing jobs when "
            "no imported transactions are linked. The local development storage "
            "backend deletes the stored file when it exists."
        ),
    )
    delete_statement_processing_jobs_for_statement(
        session,
        statement_id=statement.id,
    )
    refresh_card_charge_summaries_for_periods(
        session,
        user_id=statement.user_id,
        card_id=statement.card_id,
        period_months=charge_summary_periods,
    )
    session.delete(statement)
    session.commit()
    return result


def _get_card_for_statement_create(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> Card:
    card = session.scalar(
        select(Card).where(
            Card.id == card_id,
            Card.user_id == user_id,
        )
    )
    if card is None:
        raise AppException(
            status_code=404,
            code="CARD_NOT_FOUND",
            message="Card not found",
        )
    if card.status != "active":
        raise AppException(
            status_code=409,
            code="CARD_ARCHIVED",
            message="Archived cards cannot accept new statements",
        )
    return card


def _statement_can_retry(statement: Statement) -> bool:
    return any(
        status == "failed"
        for status in (
            statement.upload_status,
            statement.extraction_status,
            statement.categorization_status,
        )
    )
