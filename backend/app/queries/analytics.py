from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, Select, asc, case, cast, desc, func, literal, or_, select
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.category import Category
from app.models.reward_ledger import RewardLedger
from app.models.transaction import Transaction
from app.schemas.dashboard import AnalyticsFilterQuery, CardAnalyticsFilterQuery

ZERO_AMOUNT = Decimal("0.00")
UNCATEGORIZED_NAME = "Uncategorized"


@dataclass(frozen=True, slots=True)
class DashboardSummaryMetricsRow:
    total_spend: Decimal
    transaction_count: int
    needs_review_count: int


@dataclass(frozen=True, slots=True)
class SpendByCategoryRow:
    category_id: UUID | None
    category_name: str
    amount: Decimal
    transaction_count: int


@dataclass(frozen=True, slots=True)
class SpendByCardRow:
    card_id: UUID
    card_name: str
    amount: Decimal
    transaction_count: int


@dataclass(frozen=True, slots=True)
class RewardVsChargeRow:
    card_id: UUID
    card_name: str
    total_spend: Decimal
    reward_value: Decimal
    charges: Decimal
    net_value: Decimal


@dataclass(frozen=True, slots=True)
class MonthlyTrendRow:
    month: date
    total_spend: Decimal
    reward_value: Decimal
    charges: Decimal
    net_value: Decimal


@dataclass(frozen=True, slots=True)
class TopMerchantRow:
    merchant_name: str
    amount: Decimal
    transaction_count: int


@dataclass(frozen=True, slots=True)
class ChargeBreakdownRow:
    charges: Decimal
    annual_fee: Decimal
    joining_fee: Decimal
    other_charges: Decimal


@dataclass(frozen=True, slots=True)
class RewardSummaryRow:
    reward_points: Decimal
    reward_value: Decimal


def get_dashboard_summary_metrics(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> DashboardSummaryMetricsRow:
    statement = _apply_transaction_filters(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            _spend_condition(),
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("total_spend"),
            func.count(Transaction.id).label("transaction_count"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.review_required.is_(True), 1),
                        else_=0,
                    )
                ),
                0,
            ).label("needs_review_count"),
        ),
        user_id=user_id,
        filters=filters,
    )
    row = session.execute(statement).one()
    return DashboardSummaryMetricsRow(
        total_spend=row.total_spend or ZERO_AMOUNT,
        transaction_count=int(row.transaction_count or 0),
        needs_review_count=int(row.needs_review_count or 0),
    )


def get_total_spend(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> Decimal:
    statement = _apply_transaction_filters(
        select(
            func.coalesce(func.sum(Transaction.amount), 0).label("total_spend"),
        ).where(_spend_condition()),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    return session.scalar(statement) or ZERO_AMOUNT


def list_spend_by_category(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
    limit: int | None = None,
) -> list[SpendByCategoryRow]:
    category_name = func.coalesce(Category.name, literal(UNCATEGORIZED_NAME))
    amount = func.coalesce(func.sum(Transaction.amount), 0).label("amount")
    transaction_count = func.count(Transaction.id).label("transaction_count")
    statement = (
        select(
            Transaction.category_id.label("category_id"),
            category_name.label("category_name"),
            amount,
            transaction_count,
        )
        .select_from(Transaction)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(_spend_condition())
        .group_by(Transaction.category_id, category_name)
    )
    statement = _apply_transaction_filters(
        statement,
        user_id=user_id,
        filters=filters,
    ).order_by(desc(amount), asc(category_name))
    if limit is not None:
        statement = statement.limit(limit)
    rows = session.execute(statement).all()
    return [
        SpendByCategoryRow(
            category_id=row.category_id,
            category_name=row.category_name,
            amount=row.amount or ZERO_AMOUNT,
            transaction_count=int(row.transaction_count or 0),
        )
        for row in rows
    ]


def list_spend_by_card(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
    limit: int | None = None,
) -> list[SpendByCardRow]:
    amount = func.coalesce(func.sum(Transaction.amount), 0).label("amount")
    transaction_count = func.count(Transaction.id).label("transaction_count")
    statement = (
        select(
            Card.id.label("card_id"),
            Card.nickname.label("card_name"),
            amount,
            transaction_count,
        )
        .select_from(Transaction)
        .join(Card, Card.id == Transaction.card_id)
        .where(_spend_condition())
        .group_by(Card.id, Card.nickname)
    )
    statement = _apply_transaction_filters(
        statement,
        user_id=user_id,
        filters=filters,
    ).order_by(desc(amount), asc(Card.nickname))
    if limit is not None:
        statement = statement.limit(limit)
    rows = session.execute(statement).all()
    return [
        SpendByCardRow(
            card_id=row.card_id,
            card_name=row.card_name,
            amount=row.amount or ZERO_AMOUNT,
            transaction_count=int(row.transaction_count or 0),
        )
        for row in rows
    ]


def get_total_charges(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> Decimal:
    statement = _apply_transaction_filters(
        select(func.coalesce(func.sum(_signed_charge_amount()), 0).label("charges")),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    ).where(Transaction.is_card_charge.is_(True))
    return session.scalar(statement) or ZERO_AMOUNT


def get_charge_breakdown(
    session: Session,
    *,
    user_id: UUID,
    filters: CardAnalyticsFilterQuery,
    card_id: UUID,
) -> ChargeBreakdownRow:
    signed_amount = _signed_charge_amount()
    annual_fee_amount = case((Transaction.charge_type == "annual_fee", signed_amount), else_=0)
    joining_fee_amount = case((Transaction.charge_type == "joining_fee", signed_amount), else_=0)

    statement = _apply_transaction_filters(
        select(
            func.coalesce(func.sum(signed_amount), 0).label("charges"),
            func.coalesce(func.sum(annual_fee_amount), 0).label("annual_fee"),
            func.coalesce(func.sum(joining_fee_amount), 0).label("joining_fee"),
        ).where(Transaction.is_card_charge.is_(True)),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    row = session.execute(statement).one()
    total_charges = row.charges or ZERO_AMOUNT
    annual_fee = row.annual_fee or ZERO_AMOUNT
    joining_fee = row.joining_fee or ZERO_AMOUNT
    return ChargeBreakdownRow(
        charges=total_charges,
        annual_fee=annual_fee,
        joining_fee=joining_fee,
        other_charges=total_charges - annual_fee - joining_fee,
    )


def get_reward_summary(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> RewardSummaryRow:
    statement = _apply_reward_filters(
        select(
            func.coalesce(func.sum(_signed_reward_points()), 0).label("reward_points"),
            func.coalesce(func.sum(_reward_value_expression()), 0).label("reward_value"),
        )
        .select_from(RewardLedger)
        .join(Card, Card.id == RewardLedger.card_id),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    row = session.execute(statement).one()
    return RewardSummaryRow(
        reward_points=row.reward_points or ZERO_AMOUNT,
        reward_value=row.reward_value or ZERO_AMOUNT,
    )


def list_rewards_vs_charges(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
) -> list[RewardVsChargeRow]:
    spend_subquery = _apply_transaction_filters(
        select(
            Transaction.card_id.label("card_id"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_spend"),
        )
        .where(_spend_condition())
        .group_by(Transaction.card_id),
        user_id=user_id,
        filters=filters,
    ).subquery()

    charge_subquery = _apply_transaction_filters(
        select(
            Transaction.card_id.label("card_id"),
            func.coalesce(func.sum(_signed_charge_amount()), 0).label("charges"),
        )
        .where(Transaction.is_card_charge.is_(True))
        .group_by(Transaction.card_id),
        user_id=user_id,
        filters=filters,
    ).subquery()

    reward_subquery = _apply_reward_filters(
        select(
            RewardLedger.card_id.label("card_id"),
            func.coalesce(func.sum(_reward_value_expression()), 0).label("reward_value"),
        )
        .select_from(RewardLedger)
        .join(Card, Card.id == RewardLedger.card_id)
        .group_by(RewardLedger.card_id),
        user_id=user_id,
        filters=filters,
    ).subquery()

    total_spend = func.coalesce(spend_subquery.c.total_spend, 0)
    reward_value = func.coalesce(reward_subquery.c.reward_value, 0)
    charges = func.coalesce(charge_subquery.c.charges, 0)
    net_value = (reward_value - charges).label("net_value")

    statement = (
        select(
            Card.id.label("card_id"),
            Card.nickname.label("card_name"),
            total_spend.label("total_spend"),
            reward_value.label("reward_value"),
            charges.label("charges"),
            net_value,
        )
        .outerjoin(spend_subquery, spend_subquery.c.card_id == Card.id)
        .outerjoin(charge_subquery, charge_subquery.c.card_id == Card.id)
        .outerjoin(reward_subquery, reward_subquery.c.card_id == Card.id)
        .where(Card.user_id == user_id)
    )
    if filters.card_id is not None:
        statement = statement.where(Card.id == filters.card_id)

    statement = statement.where(
        or_(
            total_spend != 0,
            reward_value != 0,
            charges != 0,
        )
    ).order_by(desc(net_value), desc(reward_value), asc(Card.nickname))

    rows = session.execute(statement).all()
    return [
        RewardVsChargeRow(
            card_id=row.card_id,
            card_name=row.card_name,
            total_spend=row.total_spend or ZERO_AMOUNT,
            reward_value=row.reward_value or ZERO_AMOUNT,
            charges=row.charges or ZERO_AMOUNT,
            net_value=row.net_value or ZERO_AMOUNT,
        )
        for row in rows
    ]


def list_monthly_trend(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> list[MonthlyTrendRow]:
    spend_by_month = {
        row.month: row.amount or ZERO_AMOUNT
        for row in _list_monthly_amounts(
            session,
            user_id=user_id,
            filters=filters,
            card_id=card_id,
            source="spend",
        )
    }
    charge_by_month = {
        row.month: row.amount or ZERO_AMOUNT
        for row in _list_monthly_amounts(
            session,
            user_id=user_id,
            filters=filters,
            card_id=card_id,
            source="charges",
        )
    }
    reward_by_month = {
        row.month: row.amount or ZERO_AMOUNT
        for row in _list_monthly_reward_amounts(
            session,
            user_id=user_id,
            filters=filters,
            card_id=card_id,
        )
    }

    months = sorted(set(spend_by_month) | set(charge_by_month) | set(reward_by_month))
    return [
        MonthlyTrendRow(
            month=month,
            total_spend=spend_by_month.get(month, ZERO_AMOUNT),
            reward_value=reward_by_month.get(month, ZERO_AMOUNT),
            charges=charge_by_month.get(month, ZERO_AMOUNT),
            net_value=reward_by_month.get(month, ZERO_AMOUNT) - charge_by_month.get(month, ZERO_AMOUNT),
        )
        for month in months
    ]


def list_top_merchants(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery,
    limit: int = 10,
) -> list[TopMerchantRow]:
    merchant_name = func.coalesce(
        func.nullif(Transaction.normalized_merchant, ""),
        Transaction.raw_description,
    )
    amount = func.coalesce(func.sum(Transaction.amount), 0).label("amount")
    statement = (
        select(
            merchant_name.label("merchant_name"),
            amount,
            func.count(Transaction.id).label("transaction_count"),
        )
        .select_from(Transaction)
        .where(_spend_condition())
        .group_by(merchant_name)
    )
    statement = _apply_transaction_filters(
        statement,
        user_id=user_id,
        filters=filters,
    ).order_by(desc(amount), asc(merchant_name)).limit(limit)
    rows = session.execute(statement).all()
    return [
        TopMerchantRow(
            merchant_name=row.merchant_name,
            amount=row.amount or ZERO_AMOUNT,
            transaction_count=int(row.transaction_count or 0),
        )
        for row in rows
    ]


@dataclass(frozen=True, slots=True)
class _MonthlyAmountRow:
    month: date
    amount: Decimal


def _list_monthly_amounts(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None,
    source: str,
) -> list[_MonthlyAmountRow]:
    month_bucket = _month_bucket_expression(session, Transaction.txn_date)
    if source == "spend":
        amount_expression = Transaction.amount
        predicate = _spend_condition()
    else:
        amount_expression = _signed_charge_amount()
        predicate = Transaction.is_card_charge.is_(True)

    statement = _apply_transaction_filters(
        select(
            month_bucket.label("month"),
            func.coalesce(func.sum(amount_expression), 0).label("amount"),
        )
        .select_from(Transaction)
        .where(predicate)
        .group_by(month_bucket)
        .order_by(month_bucket),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    rows = session.execute(statement).all()
    return [
        _MonthlyAmountRow(
            month=_coerce_month_value(row.month),
            amount=row.amount or ZERO_AMOUNT,
        )
        for row in rows
    ]


def _list_monthly_reward_amounts(
    session: Session,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None,
) -> list[_MonthlyAmountRow]:
    month_bucket = _month_bucket_expression(session, RewardLedger.event_date)
    statement = _apply_reward_filters(
        select(
            month_bucket.label("month"),
            func.coalesce(func.sum(_reward_value_expression()), 0).label("amount"),
        )
        .select_from(RewardLedger)
        .join(Card, Card.id == RewardLedger.card_id)
        .group_by(month_bucket)
        .order_by(month_bucket),
        user_id=user_id,
        filters=filters,
        card_id=card_id,
    )
    rows = session.execute(statement).all()
    return [
        _MonthlyAmountRow(
            month=_coerce_month_value(row.month),
            amount=row.amount or ZERO_AMOUNT,
        )
        for row in rows
    ]


def _apply_transaction_filters(
    statement: Select,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> Select:
    statement = statement.where(
        Transaction.user_id == user_id,
        Transaction.duplicate_flag.is_(False),
    )
    scoped_card_id = card_id or getattr(filters, "card_id", None)
    if scoped_card_id is not None:
        statement = statement.where(Transaction.card_id == scoped_card_id)
    if filters.category_id is not None:
        statement = statement.where(Transaction.category_id == filters.category_id)
    if filters.from_date is not None:
        statement = statement.where(Transaction.txn_date >= filters.from_date)
    if filters.to_date is not None:
        statement = statement.where(Transaction.txn_date <= filters.to_date)
    return statement


def _apply_reward_filters(
    statement: Select,
    *,
    user_id: UUID,
    filters: AnalyticsFilterQuery | CardAnalyticsFilterQuery,
    card_id: UUID | None = None,
) -> Select:
    statement = statement.where(RewardLedger.user_id == user_id)
    scoped_card_id = card_id or getattr(filters, "card_id", None)
    if scoped_card_id is not None:
        statement = statement.where(RewardLedger.card_id == scoped_card_id)
    if filters.from_date is not None:
        statement = statement.where(RewardLedger.event_date >= filters.from_date)
    if filters.to_date is not None:
        statement = statement.where(RewardLedger.event_date <= filters.to_date)
    return statement


def _spend_condition():
    return (
        (Transaction.txn_type == "spend")
        & (Transaction.is_card_charge.is_(False))
        & (Transaction.txn_direction == "debit")
    )


def _signed_charge_amount():
    return case(
        (Transaction.txn_direction == "credit", -Transaction.amount),
        else_=Transaction.amount,
    )


def _signed_reward_points():
    points = func.coalesce(RewardLedger.reward_points, 0)
    return case(
        (RewardLedger.event_type.in_(("redeemed", "expired")), -points),
        else_=points,
    )


def _reward_value_expression():
    base_value = func.coalesce(
        RewardLedger.reward_value_estimate,
        RewardLedger.reward_points * Card.reward_conversion_rate,
        0,
    )
    return case(
        (RewardLedger.event_type.in_(("redeemed", "expired")), -base_value),
        else_=base_value,
    )


def _month_bucket_expression(session: Session, column):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "sqlite":
        return func.date(column, "start of month")
    return cast(func.date_trunc("month", column), Date)


def _coerce_month_value(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
