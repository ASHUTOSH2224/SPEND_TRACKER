from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session

from app.queries.analytics import (
    get_dashboard_summary_metrics,
    get_reward_summary,
    get_total_charges,
    get_total_spend,
    list_monthly_trend,
    list_rewards_vs_charges,
    list_spend_by_card,
    list_spend_by_category,
    list_top_merchants,
)
from app.queries.rewards import get_card_charge_summary
from app.schemas.dashboard import (
    AnalyticsFilterQuery,
    CardAnalyticsFilterQuery,
    CardSummaryCardRead,
    CardSummaryQuery,
    CardSummaryRead,
    CardTransactionListQuery,
    DashboardSummaryCardRead,
    DashboardSummaryCategoryRead,
    DashboardSummaryRead,
    MonthlyTrendRead,
    RewardVsChargesRead,
    SpendByCardRead,
    SpendByCategoryRead,
    SummaryFilterQuery,
    TopMerchantRead,
)
from app.schemas.transactions import TransactionListQuery
from app.services.cards import get_card_for_user
from app.services.transactions import list_transactions_for_user

ZERO_AMOUNT = Decimal("0.00")
ZERO_PERCENT = Decimal("0.00")
PERCENT_QUANTUM = Decimal("0.01")


def get_dashboard_summary_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: SummaryFilterQuery,
) -> DashboardSummaryRead:
    current_start, current_end = _resolve_summary_period(filters.from_date, filters.to_date)
    current_filters = AnalyticsFilterQuery(
        from_date=current_start,
        to_date=current_end,
        card_id=filters.card_id,
        category_id=filters.category_id,
    )
    previous_filters = AnalyticsFilterQuery(
        from_date=current_start - timedelta(days=(current_end - current_start).days + 1),
        to_date=current_start - timedelta(days=1),
        card_id=filters.card_id,
        category_id=filters.category_id,
    )

    metrics = get_dashboard_summary_metrics(
        session,
        user_id=user_id,
        filters=current_filters,
    )
    previous_period_spend = get_total_spend(
        session,
        user_id=user_id,
        filters=previous_filters,
    )
    reward_summary = get_reward_summary(
        session,
        user_id=user_id,
        filters=current_filters,
    )
    total_charges = get_total_charges(
        session,
        user_id=user_id,
        filters=current_filters,
    )
    top_category_row = next(
        iter(
            list_spend_by_category(
                session,
                user_id=user_id,
                filters=current_filters,
                limit=1,
            )
        ),
        None,
    )
    top_card_row = next(
        iter(
            list_spend_by_card(
                session,
                user_id=user_id,
                filters=current_filters,
                limit=1,
            )
        ),
        None,
    )

    top_category = None
    if top_category_row is not None:
        top_category = DashboardSummaryCategoryRead(
            category_id=top_category_row.category_id,
            name=top_category_row.category_name,
            amount=top_category_row.amount,
        )

    top_card = None
    if top_card_row is not None:
        top_card = DashboardSummaryCardRead(
            card_id=top_card_row.card_id,
            name=top_card_row.card_name,
            amount=top_card_row.amount,
        )

    return DashboardSummaryRead(
        total_spend=metrics.total_spend,
        previous_period_spend=previous_period_spend,
        spend_change_pct=_calculate_change_pct(
            current_value=metrics.total_spend,
            previous_value=previous_period_spend,
        ),
        total_rewards_value=reward_summary.reward_value,
        total_charges=total_charges,
        net_card_value=reward_summary.reward_value - total_charges,
        transaction_count=metrics.transaction_count,
        needs_review_count=metrics.needs_review_count,
        top_category=top_category,
        top_card=top_card,
    )


def list_dashboard_spend_by_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[SpendByCategoryRead]:
    rows = list_spend_by_category(
        session,
        user_id=user_id,
        filters=filters,
    )
    return [
        SpendByCategoryRead(
            category_id=row.category_id,
            category_name=row.category_name,
            amount=row.amount,
            transaction_count=row.transaction_count,
        )
        for row in rows
    ]


def list_dashboard_spend_by_card_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[SpendByCardRead]:
    rows = list_spend_by_card(
        session,
        user_id=user_id,
        filters=filters,
    )
    return [
        SpendByCardRead(
            card_id=row.card_id,
            card_name=row.card_name,
            amount=row.amount,
            transaction_count=row.transaction_count,
        )
        for row in rows
    ]


def list_dashboard_rewards_vs_charges_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[RewardVsChargesRead]:
    rows = list_rewards_vs_charges(
        session,
        user_id=user_id,
        filters=filters,
    )
    return [
        RewardVsChargesRead(
            card_id=row.card_id,
            card_name=row.card_name,
            total_spend=row.total_spend,
            reward_value=row.reward_value,
            charges=row.charges,
            net_value=row.net_value,
        )
        for row in rows
    ]


def list_dashboard_monthly_trend_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[MonthlyTrendRead]:
    rows = list_monthly_trend(
        session,
        user_id=user_id,
        filters=filters,
    )
    return [
        MonthlyTrendRead(
            month=row.month,
            total_spend=row.total_spend,
            reward_value=row.reward_value,
            charges=row.charges,
            net_value=row.net_value,
        )
        for row in rows
    ]


def list_dashboard_top_merchants_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[TopMerchantRead]:
    rows = list_top_merchants(
        session,
        user_id=user_id,
        filters=filters,
    )
    return [
        TopMerchantRead(
            merchant_name=row.merchant_name,
            amount=row.amount,
            transaction_count=row.transaction_count,
        )
        for row in rows
    ]


def get_card_summary_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    filters: CardSummaryQuery,
) -> CardSummaryRead:
    card = get_card_for_user(
        session,
        user_id=user_id,
        card_id=card_id,
    )
    current_start, current_end = _resolve_summary_period(filters.from_date, filters.to_date)
    summary_filters = CardAnalyticsFilterQuery(
        from_date=current_start,
        to_date=current_end,
        category_id=filters.category_id,
    )

    total_spend = get_total_spend(
        session,
        user_id=user_id,
        filters=summary_filters,
        card_id=card.id,
    )
    reward_summary = get_reward_summary(
        session,
        user_id=user_id,
        filters=summary_filters,
        card_id=card.id,
    )
    charges = get_card_charge_summary(
        session,
        user_id=user_id,
        card_id=card.id,
        from_date=current_start,
        to_date=current_end,
    )

    return CardSummaryRead(
        card=CardSummaryCardRead(
            id=card.id,
            nickname=card.nickname,
            last4=card.last4,
            issuer_name=card.issuer_name,
        ),
        total_spend=total_spend,
        eligible_spend=total_spend,
        reward_points=reward_summary.reward_points,
        reward_value=reward_summary.reward_value,
        charges=charges.total_charge_amount,
        annual_fee=charges.annual_fee_amount,
        joining_fee=charges.joining_fee_amount,
        other_charges=(
            charges.late_fee_amount
            + charges.finance_charge_amount
            + charges.emi_processing_fee_amount
            + charges.cash_advance_fee_amount
            + charges.forex_markup_amount
            + charges.tax_amount
            + charges.other_charge_amount
        ),
        net_value=reward_summary.reward_value - charges.total_charge_amount,
    )


def list_card_monthly_trend_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    filters: CardAnalyticsFilterQuery,
) -> list[MonthlyTrendRead]:
    get_card_for_user(
        session,
        user_id=user_id,
        card_id=card_id,
    )
    rows = list_monthly_trend(
        session,
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    return [
        MonthlyTrendRead(
            month=row.month,
            total_spend=row.total_spend,
            reward_value=row.reward_value,
            charges=row.charges,
            net_value=row.net_value,
        )
        for row in rows
    ]


def list_card_transactions_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    filters: CardTransactionListQuery,
):
    get_card_for_user(
        session,
        user_id=user_id,
        card_id=card_id,
    )
    transaction_filters = TransactionListQuery(
        card_id=card_id,
        category_id=filters.category_id,
        statement_id=filters.statement_id,
        from_date=filters.from_date,
        to_date=filters.to_date,
        search=filters.search,
        review_required=filters.review_required,
        is_card_charge=filters.is_card_charge,
        charge_type=filters.charge_type,
        page=filters.page,
        page_size=filters.page_size,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )
    return list_transactions_for_user(
        session,
        user_id=user_id,
        filters=transaction_filters,
    )


def _resolve_summary_period(from_date: date | None, to_date: date | None) -> tuple[date, date]:
    if from_date is not None and to_date is not None:
        return from_date, to_date

    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    return first_day, last_day


def _calculate_change_pct(*, current_value: Decimal, previous_value: Decimal) -> Decimal:
    if previous_value == 0:
        return ZERO_PERCENT
    return ((current_value - previous_value) / previous_value * Decimal("100")).quantize(
        PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
