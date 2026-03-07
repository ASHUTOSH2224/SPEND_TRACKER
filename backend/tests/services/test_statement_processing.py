from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.db.session import get_session
from app.models.statement import Statement
from app.models.statement_processing_job import StatementProcessingJob
from app.models.transaction import Transaction
from app.services.statement_jobs import process_next_statement_processing_job
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


def _create_card(client, headers: dict[str, str], *, last4: str, nickname: str) -> str:
    response = client.post(
        "/api/v1/cards",
        json=_card_payload(last4, nickname),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_category(client, headers: dict[str, str], *, name: str) -> str:
    response = client.post(
        "/api/v1/categories",
        json={"name": name, "group_name": "spend"},
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
) -> str:
    presign_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": file_name,
            "content_type": "application/pdf",
        },
        headers=headers,
    )
    assert presign_response.status_code == 200
    file_storage_key = presign_response.json()["data"]["file_storage_key"]

    create_response = client.post(
        "/api/v1/statements",
        json={
            "card_id": card_id,
            "file_name": file_name,
            "file_storage_key": file_storage_key,
            "file_type": "pdf",
            "statement_period_start": "2026-03-01",
            "statement_period_end": "2026-03-31",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    return create_response.json()["data"]["id"]


class ExplodingParser:
    def parse(self, *, statement) -> ParsedStatementResult:
        raise RuntimeError("Parser exploded")


class SingleRowParser:
    def parse(self, *, statement) -> ParsedStatementResult:
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
