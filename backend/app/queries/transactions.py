from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transactions import TransactionListQuery


@dataclass(frozen=True, slots=True)
class TransactionQueryRecord:
    transaction: Transaction
    card_name: str
    category_name: str | None


def list_transaction_records_for_user(
    session: Session,
    *,
    user_id: UUID,
    filters: TransactionListQuery,
) -> tuple[list[TransactionQueryRecord], int]:
    statement = _apply_filters(_transaction_view_statement(user_id=user_id), filters)
    total = session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    ) or 0

    sorted_statement = _apply_sorting(statement, filters)
    paginated_statement = sorted_statement.offset((filters.page - 1) * filters.page_size).limit(
        filters.page_size
    )
    rows = session.execute(paginated_statement).all()
    return [_serialize_row(row) for row in rows], total


def get_transaction_record_for_user(
    session: Session,
    *,
    user_id: UUID,
    transaction_id: UUID,
) -> TransactionQueryRecord | None:
    statement = _transaction_view_statement(user_id=user_id).where(Transaction.id == transaction_id)
    row = session.execute(statement).first()
    if row is None:
        return None
    return _serialize_row(row)


def list_transactions_by_ids_for_user(
    session: Session,
    *,
    user_id: UUID,
    transaction_ids: list[UUID],
) -> list[Transaction]:
    statement = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.id.in_(transaction_ids),
        )
        .order_by(Transaction.created_at.asc())
    )
    return list(session.scalars(statement).all())


def _transaction_view_statement(*, user_id: UUID) -> Select:
    return (
        select(
            Transaction,
            Card.nickname.label("card_name"),
            Category.name.label("category_name"),
        )
        .join(Card, Card.id == Transaction.card_id)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(Transaction.user_id == user_id)
    )


def _apply_filters(statement: Select, filters: TransactionListQuery) -> Select:
    if filters.card_id is not None:
        statement = statement.where(Transaction.card_id == filters.card_id)
    if filters.category_id is not None:
        statement = statement.where(Transaction.category_id == filters.category_id)
    if filters.statement_id is not None:
        statement = statement.where(Transaction.statement_id == filters.statement_id)
    if filters.from_date is not None:
        statement = statement.where(Transaction.txn_date >= filters.from_date)
    if filters.to_date is not None:
        statement = statement.where(Transaction.txn_date <= filters.to_date)
    if filters.search is not None:
        pattern = f"%{filters.search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Transaction.raw_description).like(pattern),
                func.lower(func.coalesce(Transaction.normalized_merchant, "")).like(pattern),
            )
        )
    if filters.review_required is not None:
        statement = statement.where(Transaction.review_required == filters.review_required)
    if filters.is_card_charge is not None:
        statement = statement.where(Transaction.is_card_charge == filters.is_card_charge)
    if filters.charge_type is not None:
        statement = statement.where(Transaction.charge_type == filters.charge_type)
    return statement


def _apply_sorting(statement: Select, filters: TransactionListQuery) -> Select:
    sort_columns = {
        "txn_date": Transaction.txn_date,
        "posted_date": Transaction.posted_date,
        "amount": Transaction.amount,
        "created_at": Transaction.created_at,
        "updated_at": Transaction.updated_at,
    }
    direction = asc if filters.sort_order == "asc" else desc
    sort_column = sort_columns[filters.sort_by]
    return statement.order_by(direction(sort_column), direction(Transaction.created_at))


def _serialize_row(row) -> TransactionQueryRecord:
    return TransactionQueryRecord(
        transaction=row[0],
        card_name=row.card_name,
        category_name=row.category_name,
    )
