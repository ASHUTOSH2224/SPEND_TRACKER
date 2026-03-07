from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.categorization_rule import CategorizationRule
from app.models.category import Category
from app.models.transaction import Transaction


@dataclass(frozen=True, slots=True)
class MerchantHistoryMatch:
    category_id: UUID
    confidence: float
    supporting_transaction_count: int


def list_active_rules_for_user(
    session: Session,
    *,
    user_id: UUID,
) -> list[CategorizationRule]:
    statement = (
        select(CategorizationRule)
        .where(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active.is_(True),
        )
        .order_by(
            CategorizationRule.priority.asc(),
            CategorizationRule.created_at.desc(),
        )
    )
    return list(session.scalars(statement).all())


def find_assignable_category_id_by_name(
    session: Session,
    *,
    user_id: UUID,
    category_name: str,
) -> UUID | None:
    statement = (
        select(Category.id)
        .where(
            Category.name == category_name,
            Category.is_archived.is_(False),
            or_(
                Category.user_id == user_id,
                Category.user_id.is_(None),
            ),
        )
        .order_by(
            case((Category.user_id == user_id, 0), else_=1),
            case((Category.is_default.is_(True), 0), else_=1),
        )
        .limit(1)
    )
    return session.scalar(statement)


def find_merchant_history_match(
    session: Session,
    *,
    user_id: UUID,
    normalized_merchant: str,
) -> MerchantHistoryMatch | None:
    if not normalized_merchant:
        return None

    statement = (
        select(
            Transaction.category_id,
            func.count(Transaction.id).label("transaction_count"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.normalized_merchant == normalized_merchant,
            Transaction.category_id.is_not(None),
            Transaction.duplicate_flag.is_(False),
        )
        .group_by(Transaction.category_id)
        .order_by(
            func.count(Transaction.id).desc(),
            func.max(Transaction.updated_at).desc(),
        )
        .limit(1)
    )
    row = session.execute(statement).first()
    if row is None or row.category_id is None:
        return None

    transaction_count = int(row.transaction_count)
    confidence = min(0.9, 0.6 + (min(transaction_count, 4) * 0.075))
    return MerchantHistoryMatch(
        category_id=row.category_id,
        confidence=confidence,
        supporting_transaction_count=transaction_count,
    )


def source_hash_exists_for_user(
    session: Session,
    *,
    user_id: UUID,
    source_hash: str,
) -> bool:
    if not source_hash:
        return False

    statement = select(Transaction.id).where(
        Transaction.user_id == user_id,
        Transaction.source_hash == source_hash,
    )
    return session.scalar(statement) is not None
