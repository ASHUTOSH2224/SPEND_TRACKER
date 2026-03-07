import argparse
import logging
import time

from app.core.config import get_settings
from app.db.session import get_session
from app.services.statement_jobs import process_next_statement_processing_job

LOGGER = logging.getLogger(__name__)


def run_once() -> bool:
    with get_session() as session:
        job = process_next_statement_processing_job(session)
        if job is None:
            return False
        LOGGER.info(
            "statement_worker_processed job_id=%s statement_id=%s status=%s attempts=%s",
            job.id,
            job.statement_id,
            job.status,
            job.attempt_count,
        )
        return True


def run_forever() -> None:
    settings = get_settings()
    while True:
        processed_any = False
        for _ in range(settings.worker_batch_size):
            processed = run_once()
            processed_any = processed_any or processed
            if not processed:
                break
        if not processed_any:
            time.sleep(settings.worker_poll_interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the statement-processing worker scaffold.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one queued statement job and exit.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.once:
        run_once()
        return
    run_forever()


if __name__ == "__main__":
    main()
