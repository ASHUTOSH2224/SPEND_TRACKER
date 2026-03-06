from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.rules import RuleCreate, RuleRead, RuleUpdate
from app.services.rules import (
    create_rule_for_user,
    disable_rule_for_user,
    list_rules_for_user,
    update_rule_for_user,
)

router = APIRouter(prefix="/rules", tags=["rules"])


def _serialize_rule(rule) -> RuleRead:
    return RuleRead.model_validate(rule)


@router.get("", response_model=ResponseEnvelope[list[RuleRead]], status_code=status.HTTP_200_OK)
def list_rules(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[RuleRead]]:
    rules = list_rules_for_user(session, user_id=current_user.id)
    return success_response([_serialize_rule(rule) for rule in rules])


@router.post("", response_model=ResponseEnvelope[RuleRead], status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RuleRead]:
    rule = create_rule_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(_serialize_rule(rule))


@router.patch(
    "/{rule_id}",
    response_model=ResponseEnvelope[RuleRead],
    status_code=status.HTTP_200_OK,
)
def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RuleRead]:
    rule = update_rule_for_user(
        session,
        user_id=current_user.id,
        rule_id=rule_id,
        payload=payload,
    )
    return success_response(_serialize_rule(rule))


@router.delete(
    "/{rule_id}",
    response_model=ResponseEnvelope[RuleRead],
    status_code=status.HTTP_200_OK,
)
def disable_rule(
    rule_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[RuleRead]:
    rule = disable_rule_for_user(
        session,
        user_id=current_user.id,
        rule_id=rule_id,
    )
    return success_response(_serialize_rule(rule))
