from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.card_charge_summary import CardChargeSummary
from app.models.reward_ledger import RewardLedger
from app.schemas.rewards import RewardLedgerListQuery


@dataclass(frozen=True, slots=True)
class CardRewardSummaryRow:
    total_points_earned: Decimal
    total_points_redeemed: Decimal
    total_points_expired: Decimal
    estimated_reward_value: Decimal
    current_balance: Decimal


@dataclass(frozen=True, slots=True)
class CardChargeSummaryRow:
    summary_period_count: int
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


def list_reward_ledgers_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: RewardLedgerListQuery,
) -> list[RewardLedger]:
    statement = select(RewardLedger).where(RewardLedger.user_id == user_id)
    if filters.card_id is not None:
        statement = statement.where(RewardLedger.card_id == filters.card_id)
    if filters.event_type is not None:
        statement = statement.where(RewardLedger.event_type == filters.event_type)
    if filters.from_date is not None:
        statement = statement.where(RewardLedger.event_date >= filters.from_date)
    if filters.to_date is not None:
        statement = statement.where(RewardLedger.event_date <= filters.to_date)

    statement = statement.order_by(RewardLedger.event_date.desc(), RewardLedger.created_at.desc())
    return list(session.scalars(statement).all())


def get_reward_ledger_for_user(
    session: Session,
    *,
    user_id: UUID,
    reward_ledger_id: UUID,
) -> RewardLedger | None:
    statement = select(RewardLedger).where(
        RewardLedger.id == reward_ledger_id,
        RewardLedger.user_id == user_id,
    )
    return session.scalar(statement)


def get_card_reward_summary(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> CardRewardSummaryRow:
    signed_points = case(
        (RewardLedger.event_type.in_(("redeemed", "expired")), -func.coalesce(RewardLedger.reward_points, 0)),
        else_=func.coalesce(RewardLedger.reward_points, 0),
    )
    row = session.execute(
        select(
            func.coalesce(
                func.sum(
                    case((RewardLedger.event_type == "earned", func.coalesce(RewardLedger.reward_points, 0)), else_=0)
                ),
                0,
            ).label("total_points_earned"),
            func.coalesce(
                func.sum(
                    case((RewardLedger.event_type == "redeemed", func.coalesce(RewardLedger.reward_points, 0)), else_=0)
                ),
                0,
            ).label("total_points_redeemed"),
            func.coalesce(
                func.sum(
                    case((RewardLedger.event_type == "expired", func.coalesce(RewardLedger.reward_points, 0)), else_=0)
                ),
                0,
            ).label("total_points_expired"),
            func.coalesce(func.sum(func.coalesce(RewardLedger.reward_value_estimate, 0)), 0).label(
                "estimated_reward_value"
            ),
            func.coalesce(func.sum(signed_points), 0).label("current_balance"),
        ).where(
            RewardLedger.user_id == user_id,
            RewardLedger.card_id == card_id,
        )
    ).one()

    return CardRewardSummaryRow(
        total_points_earned=row.total_points_earned,
        total_points_redeemed=row.total_points_redeemed,
        total_points_expired=row.total_points_expired,
        estimated_reward_value=row.estimated_reward_value,
        current_balance=row.current_balance,
    )


def get_card_charge_summary(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> CardChargeSummaryRow:
    row = session.execute(
        select(
            func.count(CardChargeSummary.id).label("summary_period_count"),
            func.coalesce(func.sum(CardChargeSummary.annual_fee_amount), 0).label("annual_fee_amount"),
            func.coalesce(func.sum(CardChargeSummary.joining_fee_amount), 0).label("joining_fee_amount"),
            func.coalesce(func.sum(CardChargeSummary.late_fee_amount), 0).label("late_fee_amount"),
            func.coalesce(func.sum(CardChargeSummary.finance_charge_amount), 0).label("finance_charge_amount"),
            func.coalesce(func.sum(CardChargeSummary.emi_processing_fee_amount), 0).label("emi_processing_fee_amount"),
            func.coalesce(func.sum(CardChargeSummary.cash_advance_fee_amount), 0).label("cash_advance_fee_amount"),
            func.coalesce(func.sum(CardChargeSummary.forex_markup_amount), 0).label("forex_markup_amount"),
            func.coalesce(func.sum(CardChargeSummary.tax_amount), 0).label("tax_amount"),
            func.coalesce(func.sum(CardChargeSummary.other_charge_amount), 0).label("other_charge_amount"),
            func.coalesce(func.sum(CardChargeSummary.total_charge_amount), 0).label("total_charge_amount"),
        ).where(
            CardChargeSummary.user_id == user_id,
            CardChargeSummary.card_id == card_id,
        )
    ).one()

    return CardChargeSummaryRow(
        summary_period_count=row.summary_period_count,
        annual_fee_amount=row.annual_fee_amount,
        joining_fee_amount=row.joining_fee_amount,
        late_fee_amount=row.late_fee_amount,
        finance_charge_amount=row.finance_charge_amount,
        emi_processing_fee_amount=row.emi_processing_fee_amount,
        cash_advance_fee_amount=row.cash_advance_fee_amount,
        forex_markup_amount=row.forex_markup_amount,
        tax_amount=row.tax_amount,
        other_charge_amount=row.other_charge_amount,
        total_charge_amount=row.total_charge_amount,
    )
