from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.reward_ledger import RewardLedger
from app.queries.rewards import get_card_charge_summary, get_card_reward_summary, get_reward_ledger_for_user, list_reward_ledgers_for_user
from app.schemas.rewards import CardChargeSummaryRead, CardRewardSummaryRead, RewardLedgerCreate, RewardLedgerListQuery, RewardLedgerUpdate
from app.services.cards import get_card_for_user
from app.services.statements import get_statement_for_user


CHARGE_SUMMARY_SOURCE = "card_charge_summaries"


def list_reward_ledgers_for_owner(
    session: Session,
    *,
    user_id: UUID,
    filters: RewardLedgerListQuery,
) -> list[RewardLedger]:
    if filters.card_id is not None:
        get_card_for_user(session, user_id=user_id, card_id=filters.card_id)
    return list_reward_ledgers_for_user(session, user_id=user_id, filters=filters)


def create_reward_ledger_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: RewardLedgerCreate,
) -> RewardLedger:
    card = get_card_for_user(session, user_id=user_id, card_id=payload.card_id)
    _validate_statement_scope(
        session,
        user_id=user_id,
        card_id=card.id,
        statement_id=payload.statement_id,
    )

    reward_ledger = RewardLedger(
        user_id=user_id,
        card_id=card.id,
        statement_id=payload.statement_id,
        event_date=payload.event_date,
        event_type=payload.event_type,
        reward_points=payload.reward_points,
        reward_value_estimate=payload.reward_value_estimate,
        source=payload.source,
        notes=payload.notes,
    )
    session.add(reward_ledger)
    session.commit()
    session.refresh(reward_ledger)
    return reward_ledger


def get_reward_ledger_for_owner(
    session: Session,
    *,
    user_id: UUID,
    reward_ledger_id: UUID,
) -> RewardLedger:
    reward_ledger = get_reward_ledger_for_user(
        session,
        user_id=user_id,
        reward_ledger_id=reward_ledger_id,
    )
    if reward_ledger is None:
        raise AppException(
            status_code=404,
            code="REWARD_LEDGER_NOT_FOUND",
            message="Reward ledger not found",
        )
    return reward_ledger


def update_reward_ledger_for_user(
    session: Session,
    *,
    user_id: UUID,
    reward_ledger_id: UUID,
    payload: RewardLedgerUpdate,
) -> RewardLedger:
    reward_ledger = get_reward_ledger_for_owner(
        session,
        user_id=user_id,
        reward_ledger_id=reward_ledger_id,
    )
    updates = payload.model_dump(exclude_unset=True)

    if "statement_id" in updates:
        _validate_statement_scope(
            session,
            user_id=user_id,
            card_id=reward_ledger.card_id,
            statement_id=updates["statement_id"],
        )

    for field_name, value in updates.items():
        setattr(reward_ledger, field_name, value)

    session.commit()
    session.refresh(reward_ledger)
    return reward_ledger


def delete_reward_ledger_for_user(
    session: Session,
    *,
    user_id: UUID,
    reward_ledger_id: UUID,
) -> RewardLedger:
    reward_ledger = get_reward_ledger_for_owner(
        session,
        user_id=user_id,
        reward_ledger_id=reward_ledger_id,
    )
    session.delete(reward_ledger)
    session.commit()
    return reward_ledger


def get_card_reward_summary_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> CardRewardSummaryRead:
    card = get_card_for_user(session, user_id=user_id, card_id=card_id)
    summary = get_card_reward_summary(session, user_id=user_id, card_id=card.id)
    return CardRewardSummaryRead(
        card_id=card.id,
        reward_type=card.reward_type,
        total_points_earned=summary.total_points_earned,
        total_points_redeemed=summary.total_points_redeemed,
        total_points_expired=summary.total_points_expired,
        estimated_reward_value=summary.estimated_reward_value,
        current_balance=summary.current_balance,
    )


def get_card_charge_summary_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> CardChargeSummaryRead:
    card = get_card_for_user(session, user_id=user_id, card_id=card_id)
    summary = get_card_charge_summary(session, user_id=user_id, card_id=card.id)
    return CardChargeSummaryRead(
        card_id=card.id,
        source=CHARGE_SUMMARY_SOURCE,
        summary_period_count=summary.summary_period_count,
        annual_fee_amount=summary.annual_fee_amount,
        joining_fee_amount=summary.joining_fee_amount,
        late_fee_amount=summary.late_fee_amount,
        finance_charge_amount=summary.finance_charge_amount,
        emi_processing_fee_amount=summary.emi_processing_fee_amount,
        cash_advance_fee_amount=summary.cash_advance_fee_amount,
        forex_markup_amount=summary.forex_markup_amount,
        tax_amount=summary.tax_amount,
        other_charge_amount=summary.other_charge_amount,
        total_charge_amount=summary.total_charge_amount,
    )


def _validate_statement_scope(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    statement_id: UUID | None,
) -> None:
    if statement_id is None:
        return

    statement = get_statement_for_user(session, user_id=user_id, statement_id=statement_id)
    if statement.card_id != card_id:
        raise AppException(
            status_code=422,
            code="INVALID_REWARD_LEDGER_STATEMENT",
            message="statement_id must belong to the selected card",
        )
