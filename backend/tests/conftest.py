from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("AUTH_PASSWORD_HASH_ITERATIONS", "1000")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "statement-files"))

    from app.core.config import clear_settings_cache
    from app.db.session import reset_session_state

    clear_settings_cache()
    reset_session_state()

    from app.db.base import Base
    from app.db.session import get_engine
    from app.main import create_app

    Base.metadata.create_all(bind=get_engine())

    with TestClient(create_app()) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=get_engine())
    reset_session_state()
    clear_settings_cache()


@pytest.fixture()
def db_session():
    from app.db.session import get_session

    with get_session() as session:
        yield session
