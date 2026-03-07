from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, case, cast, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction

ZERO_AMOUNT = Decimal("0.00")
_KNOWN_CHARGE_TYPES = (
    "annual_fee",
    "joining_fee",
    "late_fee",
    "finance_charge",
    "emi_processing_fee",
    "cash_advance_fee",
    "forex_markup",
    "tax",
)


@dataclass(frozen=True, slots=True)
class CardChargeSummaryPeriodRow:
    period_month: date
    annual_fee_amount: Decimal
    joining_fee_amount: Decimal
    late_fee_amount: Decimal
    finance_charge_amount: Decimal
    emi_processing_fee_amount: Decimal
    cash_advance_fee_amount: Decimal
    forex_markup_amount: Decimal
    tax_amount: Decimal
    other_charge_amount: Decimal
    total_charge_amount: Decimal


def list_imported_card_charge_summary_rows(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    period_months: set[date],
) -> list[CardChargeSummaryPeriodRow]:
    if not period_months:
        return []

    month_bucket = _month_bucket_expression(session)
    period_month_values = _month_bucket_values(session, period_months)
    signed_amount = _signed_charge_amount()
    statement = (
        select(
            month_bucket.label("period_month"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "annual_fee", signed_amount), else_=0)),
                0,
            ).label("annual_fee_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "joining_fee", signed_amount), else_=0)),
                0,
            ).label("joining_fee_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "late_fee", signed_amount), else_=0)),
                0,
            ).label("late_fee_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "finance_charge", signed_amount), else_=0)),
                0,
            ).label("finance_charge_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "emi_processing_fee", signed_amount), else_=0)),
                0,
            ).label("emi_processing_fee_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "cash_advance_fee", signed_amount), else_=0)),
                0,
            ).label("cash_advance_fee_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "forex_markup", signed_amount), else_=0)),
                0,
            ).label("forex_markup_amount"),
            func.coalesce(
                func.sum(case((Transaction.charge_type == "tax", signed_amount), else_=0)),
                0,
            ).label("tax_amount"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            or_(
                                Transaction.charge_type.is_(None),
                                not_(Transaction.charge_type.in_(_KNOWN_CHARGE_TYPES)),
                            ),
                            signed_amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("other_charge_amount"),
            func.coalesce(func.sum(signed_amount), 0).label("total_charge_amount"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.card_id == card_id,
            Transaction.statement_id.is_not(None),
            Transaction.is_card_charge.is_(True),
            Transaction.duplicate_flag.is_(False),
            month_bucket.in_(period_month_values),
        )
        .group_by(month_bucket)
        .order_by(month_bucket.asc())
    )
    rows = session.execute(statement).all()
    return [
        CardChargeSummaryPeriodRow(
            period_month=_coerce_month_value(row.period_month),
            annual_fee_amount=row.annual_fee_amount or ZERO_AMOUNT,
            joining_fee_amount=row.joining_fee_amount or ZERO_AMOUNT,
            late_fee_amount=row.late_fee_amount or ZERO_AMOUNT,
            finance_charge_amount=row.finance_charge_amount or ZERO_AMOUNT,
            emi_processing_fee_amount=row.emi_processing_fee_amount or ZERO_AMOUNT,
            cash_advance_fee_amount=row.cash_advance_fee_amount or ZERO_AMOUNT,
            forex_markup_amount=row.forex_markup_amount or ZERO_AMOUNT,
            tax_amount=row.tax_amount or ZERO_AMOUNT,
            other_charge_amount=row.other_charge_amount or ZERO_AMOUNT,
            total_charge_amount=row.total_charge_amount or ZERO_AMOUNT,
        )
        for row in rows
    ]


def _signed_charge_amount():
    return case(
        (Transaction.txn_direction == "credit", -Transaction.amount),
        else_=Transaction.amount,
    )


def _month_bucket_expression(session: Session):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "sqlite":
        return func.date(Transaction.txn_date, "start of month")
    return cast(func.date_trunc("month", Transaction.txn_date), Date)


def _coerce_month_value(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _month_bucket_values(session: Session, period_months: set[date]) -> list[date | str]:
    normalized_periods = sorted(period_months)
    if session.get_bind().dialect.name == "sqlite":
        return [period.isoformat() for period in normalized_periods]
    return normalized_periods
