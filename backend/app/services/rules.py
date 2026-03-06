from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.categorization_rule import CategorizationRule
from app.schemas.rules import RuleCreate, RuleUpdate
from app.services.categories import get_assignable_category_for_user


def list_rules_for_user(session: Session, *, user_id: UUID) -> list[CategorizationRule]:
    statement = (
        select(CategorizationRule)
        .where(CategorizationRule.user_id == user_id)
        .order_by(
            case((CategorizationRule.is_active.is_(True), 0), else_=1),
            CategorizationRule.priority.asc(),
            CategorizationRule.created_at.desc(),
        )
    )
    return list(session.scalars(statement).all())


def create_rule_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: RuleCreate,
) -> CategorizationRule:
    get_assignable_category_for_user(
        session,
        user_id=user_id,
        category_id=payload.assigned_category_id,
    )

    rule = CategorizationRule(
        user_id=user_id,
        **payload.model_dump(),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def get_rule_for_user(
    session: Session,
    *,
    user_id: UUID,
    rule_id: UUID,
) -> CategorizationRule:
    statement = select(CategorizationRule).where(
        CategorizationRule.id == rule_id,
        CategorizationRule.user_id == user_id,
    )
    rule = session.scalar(statement)
    if rule is None:
        raise AppException(
            status_code=404,
            code="RULE_NOT_FOUND",
            message="Rule not found",
        )
    return rule


def update_rule_for_user(
    session: Session,
    *,
    user_id: UUID,
    rule_id: UUID,
    payload: RuleUpdate,
) -> CategorizationRule:
    rule = get_rule_for_user(session, user_id=user_id, rule_id=rule_id)
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "assigned_category_id" in updates:
        get_assignable_category_for_user(
            session,
            user_id=user_id,
            category_id=updates["assigned_category_id"],
        )

    for field_name, value in updates.items():
        setattr(rule, field_name, value)

    session.commit()
    session.refresh(rule)
    return rule


def disable_rule_for_user(
    session: Session,
    *,
    user_id: UUID,
    rule_id: UUID,
) -> CategorizationRule:
    rule = get_rule_for_user(session, user_id=user_id, rule_id=rule_id)
    if rule.is_active:
        rule.is_active = False
        session.commit()
        session.refresh(rule)
    return rule
