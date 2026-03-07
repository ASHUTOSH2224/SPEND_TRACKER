import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy.engine import URL

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


for env_path in (REPO_ROOT / ".env", BACKEND_DIR / ".env"):
    _load_dotenv_file(env_path)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_env: str
    app_debug: bool
    app_version: str
    api_v1_prefix: str
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: str
    sqlalchemy_echo: bool
    auth_secret_key: str
    auth_jwt_algorithm: str
    auth_access_token_expire_minutes: int
    auth_password_hash_iterations: int
    storage_backend: str


@lru_cache
def get_settings() -> Settings:
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db = os.getenv("POSTGRES_DB", "spend_tracker")
    app_env = os.getenv("APP_ENV", "local")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = URL.create(
            drivername="postgresql+psycopg",
            username=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
        ).render_as_string(hide_password=False)

    return Settings(
        app_name=os.getenv("APP_NAME", "Spend Tracker API"),
        app_env=app_env,
        app_debug=_get_bool("APP_DEBUG", False),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_db=postgres_db,
        database_url=database_url,
        sqlalchemy_echo=_get_bool("SQLALCHEMY_ECHO", False),
        auth_secret_key=os.getenv(
            "AUTH_SECRET_KEY",
            "local-dev-secret-key-change-me",
        ),
        auth_jwt_algorithm=os.getenv("AUTH_JWT_ALGORITHM", "HS256"),
        auth_access_token_expire_minutes=int(
            os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
        auth_password_hash_iterations=int(
            os.getenv("AUTH_PASSWORD_HASH_ITERATIONS", "600000")
        ),
        storage_backend=os.getenv("STORAGE_BACKEND", "local_fake").strip().lower(),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
