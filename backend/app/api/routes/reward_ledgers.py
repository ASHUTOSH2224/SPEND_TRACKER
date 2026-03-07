from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.rewards import RewardEventType, RewardLedgerCreate, RewardLedgerListQuery, RewardLedgerRead, RewardLedgerUpdate
from app.services.rewards import (
    create_reward_ledger_for_user,
    delete_reward_ledger_for_user,
    list_reward_ledgers_for_owner,
    update_reward_ledger_for_user,
)

router = APIRouter(prefix="/reward-ledgers", tags=["reward-ledgers"])


def get_reward_ledger_list_query(
    card_id: UUID | None = None,
    event_type: RewardEventType | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> RewardLedgerListQuery:
    try:
        return RewardLedgerListQuery(
            card_id=card_id,
            event_type=event_type,
            from_date=from_date,
            to_date=to_date,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get("", response_model=ResponseEnvelope[list[RewardLedgerRead]])
def list_reward_ledgers(
    filters: RewardLedgerListQuery = Depends(get_reward_ledger_list_query),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[RewardLedgerRead]]:
    reward_ledgers = list_reward_ledgers_for_owner(
        session,
        user_id=current_user.id,
        filters=filters,
    )
    return success_response([RewardLedgerRead.model_validate(reward_ledger) for reward_ledger in reward_ledgers])


@router.post("", response_model=ResponseEnvelope[RewardLedgerRead], status_code=201)
def create_reward_ledger(
    payload: RewardLedgerCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RewardLedgerRead]:
    reward_ledger = create_reward_ledger_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(RewardLedgerRead.model_validate(reward_ledger))


@router.patch("/{reward_ledger_id}", response_model=ResponseEnvelope[RewardLedgerRead])
def update_reward_ledger(
    reward_ledger_id: UUID,
    payload: RewardLedgerUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RewardLedgerRead]:
    reward_ledger = update_reward_ledger_for_user(
        session,
        user_id=current_user.id,
        reward_ledger_id=reward_ledger_id,
        payload=payload,
    )
    return success_response(RewardLedgerRead.model_validate(reward_ledger))


@router.delete("/{reward_ledger_id}", response_model=ResponseEnvelope[RewardLedgerRead])
def delete_reward_ledger(
    reward_ledger_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RewardLedgerRead]:
    reward_ledger = delete_reward_ledger_for_user(
        session,
        user_id=current_user.id,
        reward_ledger_id=reward_ledger_id,
    )
    return success_response(RewardLedgerRead.model_validate(reward_ledger))
