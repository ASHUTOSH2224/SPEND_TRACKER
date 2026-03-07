from decimal import Decimal
from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.categorization_rule import CategorizationRule
from app.models.transaction import Transaction
from app.models.transaction_category_audit import TransactionCategoryAudit
from app.queries.transactions import (
    TransactionQueryRecord,
    get_transaction_record_for_user,
    list_transaction_records_for_user,
    list_transactions_by_ids_for_user,
)
from app.schemas.transactions import TransactionBulkUpdate, TransactionBulkUpdateResult, TransactionListQuery, TransactionUpdate
from app.services.categories import get_assignable_category_for_user

MANUAL_CATEGORY_CONFIDENCE = Decimal("1.0000")


def list_transactions_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: TransactionListQuery,
) -> tuple[list[TransactionQueryRecord], dict[str, int]]:
    records, total = list_transaction_records_for_user(
        session,
        user_id=user_id,
        filters=filters,
    )
    meta = {
        "page": filters.page,
        "page_size": filters.page_size,
        "total": total,
        "total_pages": ceil(total / filters.page_size) if total else 0,
    }
    return records, meta


def get_transaction_for_user(
    session: Session,
    *,
    user_id: UUID,
    transaction_id: UUID,
) -> TransactionQueryRecord:
    record = get_transaction_record_for_user(
        session,
        user_id=user_id,
        transaction_id=transaction_id,
    )
    if record is None:
        raise AppException(
            status_code=404,
            code="TRANSACTION_NOT_FOUND",
            message="Transaction not found",
        )
    return record


def update_transaction_for_user(
    session: Session,
    *,
    user_id: UUID,
    transaction_id: UUID,
    payload: TransactionUpdate,
) -> TransactionQueryRecord:
    transaction = _get_transaction_model_for_user(
        session,
        user_id=user_id,
        transaction_id=transaction_id,
    )
    category = None
    if payload.category_id is not None:
        category = get_assignable_category_for_user(
            session,
            user_id=user_id,
            category_id=payload.category_id,
        )

    _, audit_count = _apply_transaction_update(
        session,
        transaction=transaction,
        category_id=payload.category_id,
        review_required=payload.review_required,
        audit_source="manual_patch",
    )

    if payload.create_rule:
        assert category is not None
        session.add(
            CategorizationRule(
                user_id=user_id,
                rule_name=_build_rule_name(
                    match_value=payload.rule_match_value or "",
                    category_name=category.name,
                ),
                match_type=payload.rule_match_type,
                match_value=payload.rule_match_value or "",
                assigned_category_id=category.id,
                priority=100,
                is_active=True,
                created_from_transaction_id=transaction.id,
            )
        )

    session.commit()
    if audit_count or payload.create_rule or payload.review_required is not None or payload.category_id is not None:
        session.refresh(transaction)
    return get_transaction_for_user(session, user_id=user_id, transaction_id=transaction_id)


def bulk_update_transactions_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: TransactionBulkUpdate,
) -> TransactionBulkUpdateResult:
    if payload.category_id is not None:
        get_assignable_category_for_user(
            session,
            user_id=user_id,
            category_id=payload.category_id,
        )

    transactions = list_transactions_by_ids_for_user(
        session,
        user_id=user_id,
        transaction_ids=payload.transaction_ids,
    )
    if len(transactions) != len(payload.transaction_ids):
        raise AppException(
            status_code=404,
            code="TRANSACTION_NOT_FOUND",
            message="One or more transactions were not found",
        )

    updated_count = 0
    audit_count = 0
    for transaction in transactions:
        did_change, audit_added = _apply_transaction_update(
            session,
            transaction=transaction,
            category_id=payload.category_id,
            review_required=payload.review_required,
            audit_source="bulk_update",
        )
        updated_count += int(did_change)
        audit_count += audit_added

    session.commit()
    return TransactionBulkUpdateResult(
        updated_count=updated_count,
        audit_count=audit_count,
    )


def _get_transaction_model_for_user(
    session: Session,
    *,
    user_id: UUID,
    transaction_id: UUID,
) -> Transaction:
    transactions = list_transactions_by_ids_for_user(
        session,
        user_id=user_id,
        transaction_ids=[transaction_id],
    )
    if not transactions:
        raise AppException(
            status_code=404,
            code="TRANSACTION_NOT_FOUND",
            message="Transaction not found",
        )
    return transactions[0]


def _apply_transaction_update(
    session: Session,
    *,
    transaction: Transaction,
    category_id: UUID | None,
    review_required: bool | None,
    audit_source: str,
) -> tuple[bool, int]:
    changed = False
    audit_count = 0

    if category_id is not None and category_id != transaction.category_id:
        old_category_id = transaction.category_id
        transaction.category_id = category_id
        transaction.category_source = "manual"
        transaction.category_confidence = MANUAL_CATEGORY_CONFIDENCE
        transaction.category_explanation = None
        session.add(
            TransactionCategoryAudit(
                transaction_id=transaction.id,
                old_category_id=old_category_id,
                new_category_id=category_id,
                changed_by="user",
                source=audit_source,
            )
        )
        audit_count += 1
        changed = True

    if review_required is not None and review_required != transaction.review_required:
        transaction.review_required = review_required
        changed = True

    return changed, audit_count


def _build_rule_name(*, match_value: str, category_name: str) -> str:
    rule_name = f"{match_value} -> {category_name}"
    return rule_name[:255]
