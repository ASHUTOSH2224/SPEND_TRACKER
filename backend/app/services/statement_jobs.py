from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.statement_processing_job import StatementProcessingJob
from app.queries.statement_jobs import (
    get_active_statement_processing_job,
    get_next_queued_statement_processing_job,
)
from app.services.statement_processing.pipeline import process_statement
from app.services.statement_processing.types import (
    LLMCategoryProvider,
    StatementNormalizer,
    StatementParser,
)
from app.services.storage import UploadStorage


def enqueue_statement_processing_job(
    session: Session,
    *,
    statement_id: UUID,
    trigger_source: str,
) -> StatementProcessingJob:
    active_job = get_active_statement_processing_job(
        session,
        statement_id=statement_id,
    )
    if active_job is not None:
        return active_job

    job = StatementProcessingJob(
        statement_id=statement_id,
        trigger_source=trigger_source,
        status="queued",
        attempt_count=0,
        last_error=None,
        started_at=None,
        finished_at=None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def claim_next_statement_processing_job(session: Session) -> StatementProcessingJob | None:
    job = get_next_queued_statement_processing_job(session)
    if job is None:
        return None

    now = datetime.now(UTC)
    job.status = "running"
    job.attempt_count += 1
    job.last_error = None
    job.started_at = now
    job.finished_at = None
    session.commit()
    session.refresh(job)
    return job


def mark_statement_processing_job_completed(
    session: Session,
    *,
    job_id: UUID,
) -> StatementProcessingJob:
    job = session.get(StatementProcessingJob, job_id)
    assert job is not None
    job.status = "completed"
    job.last_error = None
    job.finished_at = datetime.now(UTC)
    session.commit()
    session.refresh(job)
    return job


def mark_statement_processing_job_failed(
    session: Session,
    *,
    job_id: UUID,
    error_message: str,
) -> StatementProcessingJob:
    job = session.get(StatementProcessingJob, job_id)
    assert job is not None
    job.status = "failed"
    job.last_error = error_message
    job.finished_at = datetime.now(UTC)
    session.commit()
    session.refresh(job)
    return job


def delete_statement_processing_jobs_for_statement(
    session: Session,
    *,
    statement_id: UUID,
) -> None:
    session.execute(
        delete(StatementProcessingJob).where(
            StatementProcessingJob.statement_id == statement_id
        )
    )


def process_next_statement_processing_job(
    session: Session,
    *,
    storage: UploadStorage | None = None,
    parser: StatementParser | None = None,
    normalizer: StatementNormalizer | None = None,
    llm_provider: LLMCategoryProvider | None = None,
) -> StatementProcessingJob | None:
    job = claim_next_statement_processing_job(session)
    if job is None:
        return None

    try:
        process_statement(
            session,
            statement_id=job.statement_id,
            storage=storage,
            parser=parser,
            normalizer=normalizer,
            llm_provider=llm_provider,
        )
    except Exception as exc:
        return mark_statement_processing_job_failed(
            session,
            job_id=job.id,
            error_message=str(exc),
        )

    return mark_statement_processing_job_completed(
        session,
        job_id=job.id,
    )
