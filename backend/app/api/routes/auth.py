from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserRead
from app.schemas.common import ResponseEnvelope, success_response
from app.services.auth import authenticate_user, create_user, issue_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_auth_payload(user: User, settings: Settings) -> AuthResponse:
    return AuthResponse(
        user=UserRead.model_validate(user),
        token=issue_access_token(user, settings),
    )


@router.post(
    "/signup",
    response_model=ResponseEnvelope[AuthResponse],
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: SignupRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ResponseEnvelope[AuthResponse]:
    user = create_user(
        session,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        settings=settings,
    )
    return success_response(_build_auth_payload(user, settings))


@router.post(
    "/login",
    response_model=ResponseEnvelope[AuthResponse],
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ResponseEnvelope[AuthResponse]:
    user = authenticate_user(
        session,
        email=payload.email,
        password=payload.password,
    )
    return success_response(_build_auth_payload(user, settings))


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserRead],
    status_code=status.HTTP_200_OK,
)
def get_me(current_user: User = Depends(get_current_user)) -> ResponseEnvelope[UserRead]:
    return success_response(UserRead.model_validate(current_user))
