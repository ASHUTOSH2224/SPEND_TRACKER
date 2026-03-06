from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import ResponseEnvelope, success_response
from app.services.categories import (
    archive_category_for_user,
    create_category_for_user,
    list_categories_for_user,
    update_category_for_user,
)

router = APIRouter(prefix="/categories", tags=["categories"])


def _serialize_category(category) -> CategoryRead:
    return CategoryRead.model_validate(category)


@router.get(
    "",
    response_model=ResponseEnvelope[list[CategoryRead]],
    status_code=status.HTTP_200_OK,
)
def list_categories(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[CategoryRead]]:
    categories = list_categories_for_user(session, user_id=current_user.id)
    return success_response([_serialize_category(category) for category in categories])


@router.post(
    "",
    response_model=ResponseEnvelope[CategoryRead],
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CategoryRead]:
    category = create_category_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(_serialize_category(category))


@router.patch(
    "/{category_id}",
    response_model=ResponseEnvelope[CategoryRead],
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CategoryRead]:
    category = update_category_for_user(
        session,
        user_id=current_user.id,
        category_id=category_id,
        payload=payload,
    )
    return success_response(_serialize_category(category))


@router.delete(
    "/{category_id}",
    response_model=ResponseEnvelope[CategoryRead],
    status_code=status.HTTP_200_OK,
)
def archive_category(
    category_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CategoryRead]:
    category = archive_category_for_user(
        session,
        user_id=current_user.id,
        category_id=category_id,
    )
    return success_response(_serialize_category(category))
