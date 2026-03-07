from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.card_charge_summary import CardChargeSummary
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.queries.charge_summaries import list_imported_card_charge_summary_rows

ZERO_AMOUNT = Decimal("0.00")


def refresh_card_charge_summaries_for_periods(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    period_months: set[date],
) -> None:
    normalized_periods = {_month_start(period_month) for period_month in period_months}
    if not normalized_periods:
        return

    session.flush()
    session.execute(
        delete(CardChargeSummary).where(
            CardChargeSummary.user_id == user_id,
            CardChargeSummary.card_id == card_id,
            CardChargeSummary.period_month.in_(sorted(normalized_periods)),
        )
    )

    for row in list_imported_card_charge_summary_rows(
        session,
        user_id=user_id,
        card_id=card_id,
        period_months=normalized_periods,
    ):
        summary = CardChargeSummary(
            user_id=user_id,
            card_id=card_id,
            period_month=row.period_month,
            annual_fee_amount=_non_negative(row.annual_fee_amount),
            joining_fee_amount=_non_negative(row.joining_fee_amount),
            late_fee_amount=_non_negative(row.late_fee_amount),
            finance_charge_amount=_non_negative(row.finance_charge_amount),
            emi_processing_fee_amount=_non_negative(row.emi_processing_fee_amount),
            cash_advance_fee_amount=_non_negative(row.cash_advance_fee_amount),
            forex_markup_amount=_non_negative(row.forex_markup_amount),
            tax_amount=_non_negative(row.tax_amount),
            other_charge_amount=_non_negative(row.other_charge_amount),
            total_charge_amount=_non_negative(row.total_charge_amount),
        )
        if summary.total_charge_amount <= ZERO_AMOUNT:
            continue
        session.add(summary)


def get_statement_charge_summary_periods(
    session: Session,
    *,
    statement: Statement,
) -> set[date]:
    periods = expand_month_range(
        start_date=statement.statement_period_start,
        end_date=statement.statement_period_end,
    )
    transaction_dates = session.scalars(
        select(Transaction.txn_date).where(Transaction.statement_id == statement.id)
    ).all()
    periods.update(_month_start(txn_date) for txn_date in transaction_dates)
    return periods


def charge_summary_periods_from_dates(txn_dates: list[date]) -> set[date]:
    return {_month_start(txn_date) for txn_date in txn_dates}


def expand_month_range(*, start_date: date, end_date: date) -> set[date]:
    periods: set[date] = set()
    current = _month_start(start_date)
    final = _month_start(end_date)
    while current <= final:
        periods.add(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return periods


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _non_negative(value: Decimal) -> Decimal:
    return value if value >= ZERO_AMOUNT else ZERO_AMOUNT
