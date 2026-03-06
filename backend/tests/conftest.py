from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

    from app.core.config import clear_settings_cache
    from app.db.session import reset_session_state

    clear_settings_cache()
    reset_session_state()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    reset_session_state()
    clear_settings_cache()
