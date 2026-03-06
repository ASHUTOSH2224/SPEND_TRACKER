from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _connect_args(database_url: str) -> dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.sqlalchemy_echo,
        pool_pre_ping=True,
        connect_args=_connect_args(settings.database_url),
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def assert_database_connection(session: Session) -> None:
    session.execute(text("SELECT 1"))


def reset_session_state() -> None:
    engine: Engine | None = None
    if get_engine.cache_info().currsize:
        engine = get_engine()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    if engine is not None:
        engine.dispose()
