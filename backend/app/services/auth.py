from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def create_user(
    session: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    settings: Settings,
) -> User:
    existing_user = get_user_by_email(session, email)
    if existing_user is not None:
        raise AppException(
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
            message="An account with this email already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(
            password,
            iterations=settings.auth_password_hash_iterations,
        ),
        full_name=full_name,
        auth_provider="local",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(
    session: Session,
    *,
    email: str,
    password: str,
) -> User:
    user = get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def issue_access_token(user: User, settings: Settings) -> str:
    return create_access_token(
        subject=str(user.id),
        secret_key=settings.auth_secret_key,
        algorithm=settings.auth_jwt_algorithm,
        expires_delta=timedelta(minutes=settings.auth_access_token_expire_minutes),
    )
