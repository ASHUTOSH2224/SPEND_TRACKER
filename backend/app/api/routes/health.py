from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import Settings, get_settings
from app.db.session import assert_database_connection
from app.schemas.common import ResponseEnvelope, success_response
from app.schemas.health import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ResponseEnvelope[HealthStatus], status_code=status.HTTP_200_OK)
def healthcheck(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ResponseEnvelope[HealthStatus]:
    assert_database_connection(session)
    payload = HealthStatus(
        status="ok",
        database="ok",
        environment=settings.app_env,
        version=settings.app_version,
    )
    return success_response(payload)
