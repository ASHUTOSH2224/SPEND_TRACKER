from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.cards import CardCreate, CardRead, CardUpdate
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.dashboard import (
    CardAnalyticsFilterQuery,
    CardSummaryQuery,
    CardSummaryRead,
    CardTransactionListQuery,
    MonthlyTrendRead,
)
from app.schemas.rewards import CardChargeSummaryRead, CardRewardSummaryRead
from app.schemas.transactions import SortOrder, TransactionCategorySummary, TransactionRead, TransactionSortBy
from app.services.analytics import (
    get_card_summary_for_user,
    list_card_monthly_trend_for_user,
    list_card_transactions_for_user,
)
from app.services.cards import (
    archive_card_for_user,
    create_card_for_user,
    get_card_for_user,
    list_cards_for_user,
    update_card_for_user,
)
from app.services.rewards import (
    get_card_charge_summary_for_user,
    get_card_reward_summary_for_user,
)

router = APIRouter(prefix="/cards", tags=["cards"])


def _serialize_card(card) -> CardRead:
    return CardRead.model_validate(card)


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


def get_card_summary_query(
    from_date: date | None = None,
    to_date: date | None = None,
    category_id: UUID | None = None,
) -> CardSummaryQuery:
    try:
        return CardSummaryQuery(
            from_date=from_date,
            to_date=to_date,
            category_id=category_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_card_analytics_filter_query(
    from_date: date | None = None,
    to_date: date | None = None,
    category_id: UUID | None = None,
) -> CardAnalyticsFilterQuery:
    try:
        return CardAnalyticsFilterQuery(
            from_date=from_date,
            to_date=to_date,
            category_id=category_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_card_transaction_list_query(
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
) -> CardTransactionListQuery:
    try:
        return CardTransactionListQuery(
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


@router.get("", response_model=ResponseEnvelope[list[CardRead]], status_code=status.HTTP_200_OK)
def list_cards(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[CardRead]]:
    cards = list_cards_for_user(session, user_id=current_user.id)
    return success_response([_serialize_card(card) for card in cards])


@router.post("", response_model=ResponseEnvelope[CardRead], status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = create_card_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(_serialize_card(card))


@router.get(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def get_card(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = get_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(_serialize_card(card))


@router.patch(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def update_card(
    card_id: UUID,
    payload: CardUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = update_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
        payload=payload,
    )
    return success_response(_serialize_card(card))


@router.delete(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def archive_card(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = archive_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(_serialize_card(card))


@router.get(
    "/{card_id}/summary",
    response_model=ResponseEnvelope[CardSummaryRead],
    status_code=status.HTTP_200_OK,
)
def get_card_summary(
    card_id: UUID,
    filters: CardSummaryQuery = Depends(get_card_summary_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardSummaryRead]:
    summary = get_card_summary_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
        filters=filters,
    )
    return success_response(summary)


@router.get(
    "/{card_id}/rewards",
    response_model=ResponseEnvelope[CardRewardSummaryRead],
    status_code=status.HTTP_200_OK,
)
def get_card_rewards(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRewardSummaryRead]:
    summary = get_card_reward_summary_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(summary)


@router.get(
    "/{card_id}/charges",
    response_model=ResponseEnvelope[CardChargeSummaryRead],
    status_code=status.HTTP_200_OK,
)
def get_card_charges(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardChargeSummaryRead]:
    summary = get_card_charge_summary_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(summary)


@router.get(
    "/{card_id}/monthly-trend",
    response_model=ResponseEnvelope[list[MonthlyTrendRead]],
    status_code=status.HTTP_200_OK,
)
def get_card_monthly_trend(
    card_id: UUID,
    filters: CardAnalyticsFilterQuery = Depends(get_card_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[MonthlyTrendRead]]:
    trend = list_card_monthly_trend_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
        filters=filters,
    )
    return success_response(trend)


@router.get(
    "/{card_id}/transactions",
    response_model=ResponseEnvelope[list[TransactionRead]],
    status_code=status.HTTP_200_OK,
)
def get_card_transactions(
    card_id: UUID,
    filters: CardTransactionListQuery = Depends(get_card_transaction_list_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[TransactionRead]]:
    records, meta = list_card_transactions_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
        filters=filters,
    )
    return success_response([_serialize_transaction(record) for record in records], meta=meta)
