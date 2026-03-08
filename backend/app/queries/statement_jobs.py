from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.statement_processing_job import StatementProcessingJob


def get_active_statement_processing_job(
    session: Session,
    *,
    statement_id: UUID,
) -> StatementProcessingJob | None:
    statement = (
        select(StatementProcessingJob)
        .where(
            StatementProcessingJob.statement_id == statement_id,
            StatementProcessingJob.status.in_(("queued", "running")),
        )
        .order_by(StatementProcessingJob.created_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def get_next_queued_statement_processing_job(
    session: Session,
) -> StatementProcessingJob | None:
    statement = (
        select(StatementProcessingJob)
        .where(StatementProcessingJob.status == "queued")
        .order_by(
            StatementProcessingJob.queued_at.asc(),
            StatementProcessingJob.created_at.asc(),
        )
        .limit(1)
    )
    return session.scalar(statement)


def has_statement_processing_job_with_trigger_source(
    session: Session,
    *,
    statement_id: UUID,
    trigger_source: str,
) -> bool:
    statement = (
        select(StatementProcessingJob.id)
        .where(
            StatementProcessingJob.statement_id == statement_id,
            StatementProcessingJob.trigger_source == trigger_source,
        )
        .limit(1)
    )
    return session.scalar(statement) is not None
