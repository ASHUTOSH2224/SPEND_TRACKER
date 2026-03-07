from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.dashboard import (
    AnalyticsFilterQuery,
    DashboardSummaryRead,
    MonthlyTrendRead,
    RewardVsChargesRead,
    SpendByCardRead,
    SpendByCategoryRead,
    SummaryFilterQuery,
    TopMerchantRead,
)
from app.services.analytics import (
    get_dashboard_summary_for_user,
    list_dashboard_monthly_trend_for_user,
    list_dashboard_rewards_vs_charges_for_user,
    list_dashboard_spend_by_card_for_user,
    list_dashboard_spend_by_category_for_user,
    list_dashboard_top_merchants_for_user,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_summary_filter_query(
    from_date: date | None = None,
    to_date: date | None = None,
    card_id: UUID | None = None,
    category_id: UUID | None = None,
) -> SummaryFilterQuery:
    try:
        return SummaryFilterQuery(
            from_date=from_date,
            to_date=to_date,
            card_id=card_id,
            category_id=category_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_analytics_filter_query(
    from_date: date | None = None,
    to_date: date | None = None,
    card_id: UUID | None = None,
    category_id: UUID | None = None,
) -> AnalyticsFilterQuery:
    try:
        return AnalyticsFilterQuery(
            from_date=from_date,
            to_date=to_date,
            card_id=card_id,
            category_id=category_id,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get(
    "/summary",
    response_model=ResponseEnvelope[DashboardSummaryRead],
    status_code=status.HTTP_200_OK,
)
def get_dashboard_summary(
    filters: SummaryFilterQuery = Depends(get_summary_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[DashboardSummaryRead]:
    summary = get_dashboard_summary_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(summary)


@router.get(
    "/spend-by-category",
    response_model=ResponseEnvelope[list[SpendByCategoryRead]],
    status_code=status.HTTP_200_OK,
)
def get_spend_by_category(
    filters: AnalyticsFilterQuery = Depends(get_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[SpendByCategoryRead]]:
    rows = list_dashboard_spend_by_category_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(rows)


@router.get(
    "/spend-by-card",
    response_model=ResponseEnvelope[list[SpendByCardRead]],
    status_code=status.HTTP_200_OK,
)
def get_spend_by_card(
    filters: AnalyticsFilterQuery = Depends(get_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[SpendByCardRead]]:
    rows = list_dashboard_spend_by_card_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(rows)


@router.get(
    "/rewards-vs-charges",
    response_model=ResponseEnvelope[list[RewardVsChargesRead]],
    status_code=status.HTTP_200_OK,
)
def get_rewards_vs_charges(
    filters: AnalyticsFilterQuery = Depends(get_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[RewardVsChargesRead]]:
    rows = list_dashboard_rewards_vs_charges_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(rows)


@router.get(
    "/monthly-trend",
    response_model=ResponseEnvelope[list[MonthlyTrendRead]],
    status_code=status.HTTP_200_OK,
)
def get_monthly_trend(
    filters: AnalyticsFilterQuery = Depends(get_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[MonthlyTrendRead]]:
    rows = list_dashboard_monthly_trend_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(rows)


@router.get(
    "/top-merchants",
    response_model=ResponseEnvelope[list[TopMerchantRead]],
    status_code=status.HTTP_200_OK,
)
def get_top_merchants(
    filters: AnalyticsFilterQuery = Depends(get_analytics_filter_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[TopMerchantRead]]:
    rows = list_dashboard_top_merchants_for_user(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response(rows)
