from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.transactions import (
    SortOrder,
    TransactionBulkUpdate,
    TransactionBulkUpdateResult,
    TransactionCategorySummary,
    TransactionListQuery,
    TransactionRead,
    TransactionSortBy,
    TransactionUpdate,
)
from app.services.transactions import (
    bulk_update_transactions_for_user,
    get_transaction_for_user,
    list_transactions_for_user,
    update_transaction_for_user,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _serialize_transaction(record) -> TransactionRead:
    transaction = record.transaction
    category = None
    if transaction.category_id is not None and record.category_name is not None:
        category = TransactionCategorySummary(
            id=transaction.category_id,
            name=record.category_name,
        )
    return TransactionRead(
        id=transaction.id,
        txn_date=transaction.txn_date,
        posted_date=transaction.posted_date,
        card_id=transaction.card_id,
        card_name=record.card_name,
        statement_id=transaction.statement_id,
        raw_description=transaction.raw_description,
        normalized_merchant=transaction.normalized_merchant,
        amount=transaction.amount,
        currency=transaction.currency,
        txn_direction=transaction.txn_direction,
        txn_type=transaction.txn_type,
        category=category,
        category_source=transaction.category_source,
        category_confidence=transaction.category_confidence,
        category_explanation=transaction.category_explanation,
        review_required=transaction.review_required,
        duplicate_flag=transaction.duplicate_flag,
        is_card_charge=transaction.is_card_charge,
        charge_type=transaction.charge_type,
        is_reward_related=transaction.is_reward_related,
        reward_points_delta=transaction.reward_points_delta,
        cashback_amount=transaction.cashback_amount,
        source_hash=transaction.source_hash,
        metadata_json=transaction.metadata_json,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


def get_transaction_list_query(
    card_id: UUID | None = None,
    category_id: UUID | None = None,
    statement_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    search: str | None = None,
    review_required: bool | None = None,
    is_card_charge: bool | None = None,
    charge_type: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    sort_by: TransactionSortBy = "txn_date",
    sort_order: SortOrder = "desc",
) -> TransactionListQuery:
    try:
        return TransactionListQuery(
            card_id=card_id,
            category_id=category_id,
            statement_id=statement_id,
            from_date=from_date,
            to_date=to_date,
            search=search,
            review_required=review_required,
            is_card_charge=is_card_charge,
            charge_type=charge_type,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get(
    "",
    response_model=ResponseEnvelope[list[TransactionRead]],
    status_code=status.HTTP_200_OK,
)
def list_transactions(
    filters: TransactionListQuery = Depends(get_transaction_list_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[TransactionRead]]:
    records, meta = list_transactions_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response([_serialize_transaction(record) for record in records], meta=meta)


@router.post(
    "/bulk-update",
    response_model=ResponseEnvelope[TransactionBulkUpdateResult],
    status_code=status.HTTP_200_OK,
)
def bulk_update_transactions(
    payload: TransactionBulkUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[TransactionBulkUpdateResult]:
    result = bulk_update_transactions_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(result)


@router.get(
    "/{transaction_id}",
    response_model=ResponseEnvelope[TransactionRead],
    status_code=status.HTTP_200_OK,
)
def get_transaction(
    transaction_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[TransactionRead]:
    record = get_transaction_for_user(
        session,
        user_id=current_user.id,
        transaction_id=transaction_id,
    )
    return success_response(_serialize_transaction(record))


@router.patch(
    "/{transaction_id}",
    response_model=ResponseEnvelope[TransactionRead],
    status_code=status.HTTP_200_OK,
)
def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[TransactionRead]:
    record = update_transaction_for_user(
        session,
        user_id=current_user.id,
        transaction_id=transaction_id,
        payload=payload,
    )
    return success_response(_serialize_transaction(record))
