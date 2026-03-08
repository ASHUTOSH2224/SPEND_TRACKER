import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.secrets import open_secret
from app.models.card import Card
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.transaction_category_audit import TransactionCategoryAudit
from app.queries.statement_processing import source_hash_exists_for_user
from app.services.charge_summaries import (
    charge_summary_periods_from_dates,
    get_statement_charge_summary_periods,
    refresh_card_charge_summaries_for_periods,
)
from app.services.statement_processing.categorization import HybridTransactionCategorizer
from app.services.statement_processing.llm import get_llm_category_provider
from app.services.statement_processing.normalization import DefaultStatementNormalizer
from app.services.statement_processing.parsers import select_statement_parser
from app.services.statement_processing.types import (
    LLMCategoryProvider,
    StatementNormalizer,
    StatementFilePayload,
    StatementParser,
)
from app.services.storage import UploadStorage, build_upload_storage

LOGGER = logging.getLogger(__name__)


def process_statement(
    session: Session,
    *,
    statement_id: UUID,
    storage: UploadStorage | None = None,
    parser: StatementParser | None = None,
    normalizer: StatementNormalizer | None = None,
    llm_provider: LLMCategoryProvider | None = None,
) -> Statement:
    settings = get_settings()
    statement = session.get(Statement, statement_id)
    if statement is None:
        raise ValueError(f"Statement {statement_id} not found")
    card = session.get(Card, statement.card_id)
    if card is None:
        raise ValueError(f"Card {statement.card_id} not found for statement {statement_id}")

    parser_impl = parser or select_statement_parser(
        statement=statement,
        issuer_name=card.issuer_name,
    )
    normalizer_impl = normalizer or DefaultStatementNormalizer()
    storage_impl = storage or build_upload_storage(settings)
    categorizer = HybridTransactionCategorizer(
        session,
        llm_provider=llm_provider or get_llm_category_provider(),
    )

    LOGGER.info("statement_processing_started statement_id=%s", statement_id)
    _mark_extraction_running(session, statement)
    charge_summary_periods = get_statement_charge_summary_periods(
        session,
        statement=statement,
    )
    statement_transaction_ids = (
        select(Transaction.id).where(Transaction.statement_id == statement_id)
    )
    session.execute(
        delete(TransactionCategoryAudit).where(
            TransactionCategoryAudit.transaction_id.in_(statement_transaction_ids)
        )
    )
    session.execute(
        delete(Transaction).where(Transaction.statement_id == statement_id)
    )
    refresh_card_charge_summaries_for_periods(
        session,
        user_id=statement.user_id,
        card_id=statement.card_id,
        period_months=charge_summary_periods,
    )
    session.commit()

    try:
        if not storage_impl.is_owned_key(
            user_id=statement.user_id,
            file_storage_key=statement.file_storage_key,
        ):
            raise ValueError("file_storage_key must belong to the statement user")
        statement_file = StatementFilePayload(
            file_storage_key=statement.file_storage_key,
            file_name=statement.file_name,
            content_bytes=storage_impl.get_object_bytes(
                file_storage_key=statement.file_storage_key
            ),
            password=(
                open_secret(
                    statement.file_password_encrypted,
                    secret_key=settings.statement_secret_key,
                )
                if statement.file_password_encrypted is not None
                else None
            ),
        )
        parsed_statement = parser_impl.parse(
            statement=statement,
            statement_file=statement_file,
        )
        normalized_rows = normalizer_impl.normalize(
            statement=statement,
            parsed_statement=parsed_statement,
        )
    except Exception as exc:
        session.rollback()
        _mark_failed(
            session,
            statement_id=statement_id,
            failure_stage="extraction",
            error_message=str(exc),
        )
        LOGGER.exception(
            "statement_processing_failed statement_id=%s stage=extraction",
            statement_id,
        )
        raise

    _mark_categorization_running(session, statement_id=statement_id)

    try:
        refreshed_statement = session.get(Statement, statement_id)
        assert refreshed_statement is not None

        seen_source_hashes: set[str] = set()
        transaction_count = 0
        imported_charge_dates: list = []
        for normalized_row in normalized_rows:
            decision = categorizer.categorize(
                user_id=refreshed_statement.user_id,
                normalized_row=normalized_row,
            )
            duplicate_flag = _is_duplicate(
                session,
                user_id=refreshed_statement.user_id,
                source_hash=normalized_row.source_hash,
                seen_source_hashes=seen_source_hashes,
            )
            if normalized_row.source_hash:
                seen_source_hashes.add(normalized_row.source_hash)
            if normalized_row.is_card_charge:
                imported_charge_dates.append(normalized_row.txn_date)

            session.add(
                Transaction(
                    user_id=refreshed_statement.user_id,
                    card_id=refreshed_statement.card_id,
                    statement_id=refreshed_statement.id,
                    txn_date=normalized_row.txn_date,
                    posted_date=normalized_row.posted_date,
                    raw_description=normalized_row.raw_description,
                    normalized_merchant=normalized_row.normalized_merchant,
                    amount=normalized_row.amount,
                    currency=normalized_row.currency,
                    txn_direction=normalized_row.txn_direction,
                    txn_type=normalized_row.txn_type,
                    category_id=decision.category_id,
                    category_source=decision.category_source,
                    category_confidence=decision.category_confidence,
                    category_explanation=decision.category_explanation,
                    review_required=decision.review_required,
                    duplicate_flag=duplicate_flag,
                    is_card_charge=normalized_row.is_card_charge,
                    charge_type=normalized_row.charge_type,
                    is_reward_related=normalized_row.is_reward_related,
                    reward_points_delta=normalized_row.reward_points_delta,
                    cashback_amount=normalized_row.cashback_amount,
                    source_hash=normalized_row.source_hash,
                    metadata_json=normalized_row.metadata_json,
                )
            )
            transaction_count += 1

        refresh_card_charge_summaries_for_periods(
            session,
            user_id=refreshed_statement.user_id,
            card_id=refreshed_statement.card_id,
            period_months=charge_summary_periods
            | charge_summary_periods_from_dates(imported_charge_dates),
        )
        refreshed_statement.upload_status = "completed"
        refreshed_statement.extraction_status = "completed"
        refreshed_statement.categorization_status = "completed"
        refreshed_statement.transaction_count = transaction_count
        refreshed_statement.processing_error = None
        session.commit()
        session.refresh(refreshed_statement)
        LOGGER.info(
            "statement_processing_completed statement_id=%s transaction_count=%s",
            statement_id,
            transaction_count,
        )
        return refreshed_statement
    except Exception as exc:
        session.rollback()
        _mark_failed(
            session,
            statement_id=statement_id,
            failure_stage="categorization",
            error_message=str(exc),
        )
        LOGGER.exception(
            "statement_processing_failed statement_id=%s stage=categorization",
            statement_id,
        )
        raise


def _mark_extraction_running(session: Session, statement: Statement) -> None:
    statement.upload_status = "processing"
    statement.extraction_status = "running"
    statement.categorization_status = "pending"
    statement.transaction_count = 0
    statement.processing_error = None
    session.commit()
    session.refresh(statement)


def _mark_categorization_running(session: Session, *, statement_id: UUID) -> None:
    statement = session.get(Statement, statement_id)
    assert statement is not None
    statement.upload_status = "processing"
    statement.extraction_status = "completed"
    statement.categorization_status = "running"
    statement.processing_error = None
    session.commit()
    session.refresh(statement)


def _mark_failed(
    session: Session,
    *,
    statement_id: UUID,
    failure_stage: str,
    error_message: str,
) -> None:
    statement = session.get(Statement, statement_id)
    assert statement is not None

    statement.upload_status = "failed"
    statement.transaction_count = 0
    statement.processing_error = error_message[:2000]

    if failure_stage == "categorization":
        statement.extraction_status = "completed"
        statement.categorization_status = "failed"
    else:
        statement.extraction_status = "failed"
        statement.categorization_status = "pending"

    session.commit()
    session.refresh(statement)


def _is_duplicate(
    session: Session,
    *,
    user_id: UUID,
    source_hash: str,
    seen_source_hashes: set[str],
) -> bool:
    if not source_hash:
        return False
    if source_hash in seen_source_hashes:
        return True
    return source_hash_exists_for_user(
        session,
        user_id=user_id,
        source_hash=source_hash,
    )
