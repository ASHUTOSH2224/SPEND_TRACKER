from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_session
from app.core.config import get_settings
from app.models.card_charge_summary import CardChargeSummary
from app.models.statement import Statement
from app.models.statement_processing_job import StatementProcessingJob
from app.models.transaction import Transaction
from app.services.storage import build_upload_storage
from app.services.statement_jobs import process_next_statement_processing_job
from app.services.statement_processing.pipeline import process_statement
from app.services.statement_processing.types import ParsedStatementResult, ParsedTransactionRow


def _auth_context(client, *, email: str, full_name: str) -> tuple[dict[str, str], str]:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "strong-password",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    return headers, me_response.json()["data"]["id"]


def _card_payload(last4: str, nickname: str) -> dict[str, object]:
    return {
        "nickname": nickname,
        "issuer_name": "HDFC",
        "network": "Visa",
        "last4": last4,
        "statement_cycle_day": 12,
        "annual_fee_expected": 12500,
        "joining_fee_expected": 12500,
        "reward_program_name": "Infinia Rewards",
        "reward_type": "points",
        "reward_conversion_rate": "0.5000",
        "reward_rule_config_json": {"base_rate": 3},
    }


def _create_card(
    client,
    headers: dict[str, str],
    *,
    last4: str,
    nickname: str,
    issuer_name: str = "HDFC",
) -> str:
    response = client.post(
        "/api/v1/cards",
        json={**_card_payload(last4, nickname), "issuer_name": issuer_name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_category(
    client,
    headers: dict[str, str],
    *,
    name: str,
    group_name: str = "spend",
) -> str:
    response = client.post(
        "/api/v1/categories",
        json={"name": name, "group_name": group_name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_rule(
    client,
    headers: dict[str, str],
    *,
    category_id: str,
    rule_name: str,
    match_value: str,
) -> str:
    response = client.post(
        "/api/v1/rules",
        json={
            "rule_name": rule_name,
            "match_type": "description_contains",
            "match_value": match_value,
            "assigned_category_id": category_id,
            "priority": 10,
            "is_active": True,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_statement(
    client,
    headers: dict[str, str],
    *,
    card_id: str,
    file_name: str,
    file_type: str = "pdf",
    content_type: str = "application/pdf",
    file_bytes: bytes | None = None,
) -> str:
    presign_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": file_name,
            "content_type": content_type,
        },
        headers=headers,
    )
    assert presign_response.status_code == 200
    presign_data = presign_response.json()["data"]
    upload_response = client.put(
        presign_data["upload_url"],
        content=(
            file_bytes
            if file_bytes is not None
            else (
                b"%PDF-1.7 test statement"
                if file_type == "pdf"
                else b"Transaction Date,Description,Debit,Credit\n"
            )
        ),
        headers={
            **headers,
            "content-type": content_type,
        },
    )
    assert upload_response.status_code == 200
    file_storage_key = presign_data["file_storage_key"]

    create_response = client.post(
        "/api/v1/statements",
        json={
            "card_id": card_id,
            "file_name": file_name,
            "file_storage_key": file_storage_key,
            "file_type": file_type,
            "statement_period_start": "2026-03-01",
            "statement_period_end": "2026-03-31",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    return create_response.json()["data"]["id"]


def _hdfc_csv_bytes(*rows: str) -> bytes:
    header = "Transaction Date,Post Date,Description,Debit,Credit,Currency,Merchant\n"
    return (header + "\n".join(rows) + "\n").encode("utf-8")


class ExplodingParser:
    def parse(self, *, statement, statement_file) -> ParsedStatementResult:
        del statement, statement_file
        raise RuntimeError("Parser exploded")


class SingleRowParser:
    def parse(self, *, statement, statement_file) -> ParsedStatementResult:
        del statement, statement_file
        return ParsedStatementResult(
            parser_name="single-row",
            rows=[
                ParsedTransactionRow(
                    txn_date=date(2026, 3, 5),
                    posted_date=date(2026, 3, 6),
                    description="SWIGGY BANGALORE ORDER",
                    amount=Decimal("540.00"),
                    merchant=None,
                    currency="INR",
                    txn_direction="debit",
                    metadata={"line_number": 1},
                )
            ],
        )


class FileAwareNoOpParser:
    def __init__(self) -> None:
        self.seen_bytes: bytes | None = None

    def parse(self, *, statement, statement_file) -> ParsedStatementResult:
        del statement
        self.seen_bytes = statement_file.content_bytes
        return ParsedStatementResult(parser_name="file-aware-noop", rows=[])


def test_statement_create_enqueues_job_and_worker_completes_noop_processing(client) -> None:
    headers, _ = _auth_context(
        client,
        email="owner@example.com",
        full_name="Owner",
    )
    card_id = _create_card(client, headers, last4="1234", nickname="HDFC Infinia")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="march_2026.pdf",
    )

    with get_session() as session:
        queued_job = session.scalar(
            select(StatementProcessingJob).where(
                StatementProcessingJob.statement_id == UUID(statement_id)
            )
        )
        assert queued_job is not None
        assert queued_job.status == "queued"
        assert queued_job.trigger_source == "create"

    with get_session() as session:
        processed_job = process_next_statement_processing_job(session)
        assert processed_job is not None
        assert processed_job.status == "completed"
        assert processed_job.attempt_count == 1

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.upload_status == "completed"
        assert statement.extraction_status == "completed"
        assert statement.categorization_status == "completed"
        assert statement.transaction_count == 0
        assert statement.processing_error is None


def test_statement_processing_failure_marks_statement_failed_and_retry_requeues_job(client) -> None:
    headers, _ = _auth_context(
        client,
        email="failure@example.com",
        full_name="Failure Case",
    )
    card_id = _create_card(client, headers, last4="1111", nickname="Failing Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="failure.pdf",
    )

    with get_session() as session:
        failed_job = process_next_statement_processing_job(
            session,
            parser=ExplodingParser(),
        )
        assert failed_job is not None
        assert failed_job.status == "failed"
        assert failed_job.attempt_count == 1
        assert failed_job.last_error == "Parser exploded"

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.upload_status == "failed"
        assert statement.extraction_status == "failed"
        assert statement.categorization_status == "pending"
        assert statement.transaction_count == 0
        assert statement.processing_error == "Parser exploded"

    retry_response = client.post(
        f"/api/v1/statements/{statement_id}/retry",
        headers=headers,
    )
    assert retry_response.status_code == 200
    retry_data = retry_response.json()["data"]
    assert retry_data["upload_status"] == "uploaded"
    assert retry_data["extraction_status"] == "pending"
    assert retry_data["categorization_status"] == "pending"
    assert retry_data["processing_error"] is None

    with get_session() as session:
        jobs = list(
            session.scalars(
                select(StatementProcessingJob)
                .where(StatementProcessingJob.statement_id == UUID(statement_id))
                .order_by(StatementProcessingJob.created_at.asc())
            ).all()
        )
        assert len(jobs) == 2
        assert jobs[0].trigger_source == "create"
        assert jobs[0].status == "failed"
        assert jobs[1].trigger_source == "retry"
        assert jobs[1].status == "queued"


def test_statement_processing_persists_rule_based_categorization_fields(client) -> None:
    headers, _ = _auth_context(
        client,
        email="rules@example.com",
        full_name="Rules Case",
    )
    card_id = _create_card(client, headers, last4="2222", nickname="Rules Card")
    category_id = _create_category(client, headers, name="Food & Dining")
    _create_rule(
        client,
        headers,
        category_id=category_id,
        rule_name="Swiggy to Food",
        match_value="SWIGGY",
    )
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="rules.pdf",
    )

    with get_session() as session:
        processed_job = process_next_statement_processing_job(
            session,
            parser=SingleRowParser(),
        )
        assert processed_job is not None
        assert processed_job.status == "completed"

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.upload_status == "completed"
        assert statement.transaction_count == 1

        transaction = session.scalar(
            select(Transaction).where(Transaction.statement_id == UUID(statement_id))
        )
        assert transaction is not None
        assert transaction.category_id == UUID(category_id)
        assert transaction.category_source == "rule"
        assert transaction.category_confidence == Decimal("0.9500")
        assert transaction.category_explanation == "Matched rule 'Swiggy to Food'"
        assert transaction.review_required is False
        assert transaction.duplicate_flag is False


def test_statement_processing_reads_uploaded_file_bytes(client) -> None:
    headers, _ = _auth_context(
        client,
        email="files@example.com",
        full_name="Files Case",
    )
    card_id = _create_card(client, headers, last4="3333", nickname="File Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="march_2026.pdf",
        file_bytes=b"statement-bytes-for-worker",
    )
    parser = FileAwareNoOpParser()

    with get_session() as session:
        processed_job = process_next_statement_processing_job(
            session,
            parser=parser,
        )
        assert processed_job is not None
        assert processed_job.status == "completed"

    assert parser.seen_bytes == b"statement-bytes-for-worker"


def test_hdfc_csv_processing_imports_transactions_and_preserves_parser_metadata(client) -> None:
    headers, _ = _auth_context(
        client,
        email="csv@example.com",
        full_name="CSV Case",
    )
    card_id = _create_card(client, headers, last4="4444", nickname="CSV Card")
    category_id = _create_category(client, headers, name="Food & Dining")
    _create_category(client, headers, name="Annual Fee", group_name="charges")
    _create_rule(
        client,
        headers,
        category_id=category_id,
        rule_name="Swiggy to Food",
        match_value="SWIGGY",
    )
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="march_2026.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=_hdfc_csv_bytes(
            "05/03/2026,06/03/2026,SWIGGY BANGALORE ORDER,540.00,,INR,Swiggy",
            "07/03/2026,08/03/2026,ANNUAL FEE 2026,1500.00,,INR,HDFC",
            "10/03/2026,11/03/2026,AMAZON REFUND,,200.00,INR,Amazon",
        ),
    )

    with get_session() as session:
        processed_job = process_next_statement_processing_job(session)
        assert processed_job is not None
        assert processed_job.status == "completed"

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.upload_status == "completed"
        assert statement.extraction_status == "completed"
        assert statement.categorization_status == "completed"
        assert statement.transaction_count == 3

        transactions = list(
            session.scalars(
                select(Transaction)
                .where(Transaction.statement_id == UUID(statement_id))
                .order_by(Transaction.txn_date.asc(), Transaction.raw_description.asc())
            ).all()
        )
        assert len(transactions) == 3

        annual_fee_txn = next(
            transaction
            for transaction in transactions
            if transaction.raw_description == "ANNUAL FEE 2026"
        )
        assert annual_fee_txn.txn_type == "charge"
        assert annual_fee_txn.is_card_charge is True
        assert annual_fee_txn.charge_type == "annual_fee"
        assert annual_fee_txn.category_source == "rule"
        assert annual_fee_txn.category_explanation == "Matched charge keyword for annual fee"
        assert annual_fee_txn.review_required is False

        refund_txn = next(
            transaction
            for transaction in transactions
            if transaction.raw_description == "AMAZON REFUND"
        )
        assert refund_txn.txn_direction == "credit"
        assert refund_txn.txn_type == "refund"
        assert refund_txn.is_card_charge is False
        assert refund_txn.duplicate_flag is False
        assert refund_txn.review_required is True

        swiggy_txn = next(
            transaction
            for transaction in transactions
            if transaction.raw_description == "SWIGGY BANGALORE ORDER"
        )
        assert swiggy_txn.category_id == UUID(category_id)
        assert swiggy_txn.category_source == "rule"
        assert swiggy_txn.category_confidence == Decimal("0.9500")
        assert swiggy_txn.duplicate_flag is False
        assert swiggy_txn.metadata_json == {
            "parser_name": "hdfc_credit_card_csv_v1",
            "raw_metadata": {
                "line_number": 2,
                "raw_row": {
                    "Transaction Date": "05/03/2026",
                    "Post Date": "06/03/2026",
                    "Description": "SWIGGY BANGALORE ORDER",
                    "Debit": "540.00",
                    "Credit": "",
                    "Currency": "INR",
                    "Merchant": "Swiggy",
                },
            },
        }


def test_hdfc_csv_processing_marks_duplicate_reimports(client) -> None:
    headers, _ = _auth_context(
        client,
        email="dupes@example.com",
        full_name="Duplicates Case",
    )
    card_id = _create_card(client, headers, last4="5555", nickname="Duplicate Card")
    csv_bytes = _hdfc_csv_bytes(
        "05/03/2026,06/03/2026,SWIGGY BANGALORE ORDER,540.00,,INR,Swiggy"
    )

    first_statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="march_2026_first.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=csv_bytes,
    )
    second_statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="march_2026_second.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=csv_bytes,
    )

    with get_session() as session:
        first_job = process_next_statement_processing_job(session)
        second_job = process_next_statement_processing_job(session)
        assert first_job is not None
        assert first_job.status == "completed"
        assert second_job is not None
        assert second_job.status == "completed"

    with get_session() as session:
        first_transaction = session.scalar(
            select(Transaction).where(Transaction.statement_id == UUID(first_statement_id))
        )
        second_transaction = session.scalar(
            select(Transaction).where(Transaction.statement_id == UUID(second_statement_id))
        )
        assert first_transaction is not None
        assert second_transaction is not None
        assert first_transaction.duplicate_flag is False
        assert second_transaction.duplicate_flag is True
        assert first_transaction.source_hash == second_transaction.source_hash


def test_hdfc_csv_credit_rows_become_refunds_without_colliding_with_debits(client) -> None:
    headers, _ = _auth_context(
        client,
        email="refunds@example.com",
        full_name="Refund Case",
    )
    card_id = _create_card(client, headers, last4="7777", nickname="Refund Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="refunds_2026.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=_hdfc_csv_bytes(
            "12/03/2026,12/03/2026,MERCHANT REVERSAL,250.00,,INR,Merchant",
            "12/03/2026,12/03/2026,MERCHANT REVERSAL,,250.00,INR,Merchant",
        ),
    )

    with get_session() as session:
        processed_job = process_next_statement_processing_job(session)
        assert processed_job is not None
        assert processed_job.status == "completed"

    with get_session() as session:
        transactions = list(
            session.scalars(
                select(Transaction)
                .where(Transaction.statement_id == UUID(statement_id))
                .order_by(Transaction.txn_direction.asc())
            ).all()
        )
        assert len(transactions) == 2

        debit_txn = next(
            transaction for transaction in transactions if transaction.txn_direction == "debit"
        )
        credit_txn = next(
            transaction for transaction in transactions if transaction.txn_direction == "credit"
        )
        assert debit_txn.txn_type == "spend"
        assert credit_txn.txn_type == "refund"
        assert debit_txn.duplicate_flag is False
        assert credit_txn.duplicate_flag is False
        assert debit_txn.source_hash != credit_txn.source_hash


def test_hdfc_csv_parser_failure_marks_statement_failed(client) -> None:
    headers, _ = _auth_context(
        client,
        email="badcsv@example.com",
        full_name="Bad CSV Case",
    )
    card_id = _create_card(client, headers, last4="6666", nickname="Bad CSV Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="bad_march_2026.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=(
            "Transaction Date,Description,Debit,Credit\n"
            "05/03/2026,SWIGGY BANGALORE ORDER,540.00,\n"
        ).encode("utf-8"),
    )

    with get_session() as session:
        failed_job = process_next_statement_processing_job(session)
        assert failed_job is not None
        assert failed_job.status == "failed"
        assert (
            failed_job.last_error
            == "Unsupported HDFC CSV format: missing required columns posted_date"
        )

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.upload_status == "failed"
        assert statement.extraction_status == "failed"
        assert statement.categorization_status == "pending"
        assert statement.transaction_count == 0
        assert (
            statement.processing_error
            == "Unsupported HDFC CSV format: missing required columns posted_date"
        )


def test_statement_processing_upserts_card_charge_summaries_from_imported_transactions(client) -> None:
    headers, _ = _auth_context(
        client,
        email="charges@example.com",
        full_name="Charges Case",
    )
    card_id = _create_card(client, headers, last4="8888", nickname="Charge Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="charges_2026.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=_hdfc_csv_bytes(
            "05/03/2026,06/03/2026,ANNUAL FEE 2026,1500.00,,INR,HDFC",
            "06/03/2026,06/03/2026,FINANCE CHARGE,30.00,,INR,HDFC",
            "07/03/2026,07/03/2026,BANK CHARGE GST,270.00,,INR,HDFC",
            "08/03/2026,08/03/2026,SWIGGY ORDER,500.00,,INR,Swiggy",
        ),
    )

    with get_session() as session:
        processed_job = process_next_statement_processing_job(session)
        assert processed_job is not None
        assert processed_job.status == "completed"

    with get_session() as session:
        summary = session.scalar(
            select(CardChargeSummary).where(
                CardChargeSummary.card_id == UUID(card_id),
                CardChargeSummary.period_month == date(2026, 3, 1),
            )
        )
        assert summary is not None
        assert summary.annual_fee_amount == Decimal("1500.00")
        assert summary.finance_charge_amount == Decimal("30.00")
        assert summary.tax_amount == Decimal("270.00")
        assert summary.total_charge_amount == Decimal("1800.00")

        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        assert statement.transaction_count == 4


def test_statement_retry_rebuilds_and_clears_card_charge_summaries(client) -> None:
    headers, _ = _auth_context(
        client,
        email="charge-retry@example.com",
        full_name="Charge Retry Case",
    )
    card_id = _create_card(client, headers, last4="9999", nickname="Retry Card")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="retry_charges_2026.csv",
        file_type="csv",
        content_type="text/csv",
        file_bytes=_hdfc_csv_bytes(
            "05/03/2026,06/03/2026,ANNUAL FEE 2026,1500.00,,INR,HDFC",
            "07/03/2026,07/03/2026,BANK CHARGE GST,270.00,,INR,HDFC",
        ),
    )

    with get_session() as session:
        first_job = process_next_statement_processing_job(session)
        assert first_job is not None
        assert first_job.status == "completed"

    with get_session() as session:
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        storage = build_upload_storage(get_settings())
        storage.store_object(
            file_storage_key=statement.file_storage_key,
            content=_hdfc_csv_bytes(
                "10/03/2026,10/03/2026,SWIGGY ORDER,540.00,,INR,Swiggy"
            ),
        )
        statement.upload_status = "failed"
        statement.extraction_status = "failed"
        statement.categorization_status = "pending"
        session.commit()

    retry_response = client.post(
        f"/api/v1/statements/{statement_id}/retry",
        headers=headers,
    )
    assert retry_response.status_code == 200

    with get_session() as session:
        retried_job = process_next_statement_processing_job(session)
        assert retried_job is not None
        assert retried_job.status == "completed"

    with get_session() as session:
        summaries = list(
            session.scalars(
                select(CardChargeSummary).where(
                    CardChargeSummary.card_id == UUID(card_id)
                )
            ).all()
        )
        assert summaries == []

        transactions = list(
            session.scalars(
                select(Transaction)
                .where(Transaction.statement_id == UUID(statement_id))
                .order_by(Transaction.txn_date.asc())
            ).all()
        )
        assert len(transactions) == 1
        assert transactions[0].is_card_charge is False
