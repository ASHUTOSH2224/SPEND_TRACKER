import re
from uuid import UUID

from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.category import Category
from app.schemas.categories import CategoryCreate, CategoryUpdate

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify_category_name(name: str) -> str:
    slug = _SLUG_PATTERN.sub("-", name.strip().lower()).strip("-")
    return slug or "category"


def _category_scope_order():
    return case(
        (Category.group_name == "spend", 0),
        (Category.group_name == "charges", 1),
        else_=2,
    )


def list_categories_for_user(session: Session, *, user_id: UUID) -> list[Category]:
    statement = (
        select(Category)
        .where(
            or_(
                Category.user_id == user_id,
                and_(
                    Category.user_id.is_(None),
                    Category.is_default.is_(True),
                ),
            )
        )
        .order_by(
            _category_scope_order(),
            case((Category.is_archived.is_(False), 0), else_=1),
            case((Category.is_default.is_(True), 0), else_=1),
            Category.name.asc(),
        )
    )
    return list(session.scalars(statement).all())


def create_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: CategoryCreate,
) -> Category:
    category = Category(
        user_id=user_id,
        name=payload.name,
        slug=slugify_category_name(payload.name),
        group_name=payload.group_name,
        is_default=False,
        is_archived=False,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def get_owned_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    category_id: UUID,
) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise AppException(
            status_code=404,
            code="CATEGORY_NOT_FOUND",
            message="Category not found",
        )

    if category.is_default:
        raise AppException(
            status_code=403,
            code="CATEGORY_READ_ONLY",
            message="Default categories cannot be modified",
        )

    if category.user_id != user_id:
        raise AppException(
            status_code=404,
            code="CATEGORY_NOT_FOUND",
            message="Category not found",
        )

    return category


def get_assignable_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    category_id: UUID,
) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise AppException(
            status_code=422,
            code="INVALID_ASSIGNED_CATEGORY",
            message="Assigned category is invalid",
        )

    is_default_category = category.is_default and category.user_id is None
    is_owned_category = category.user_id == user_id and not category.is_default
    if category.is_archived or not (is_default_category or is_owned_category):
        raise AppException(
            status_code=422,
            code="INVALID_ASSIGNED_CATEGORY",
            message="Assigned category is invalid",
        )

    return category


def update_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    category_id: UUID,
    payload: CategoryUpdate,
) -> Category:
    category = get_owned_category_for_user(session, user_id=user_id, category_id=category_id)
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "name" in updates:
        category.name = updates["name"]
        category.slug = slugify_category_name(updates["name"])
    if "is_archived" in updates:
        category.is_archived = updates["is_archived"]

    session.commit()
    session.refresh(category)
    return category


def archive_category_for_user(
    session: Session,
    *,
    user_id: UUID,
    category_id: UUID,
) -> Category:
    category = get_owned_category_for_user(session, user_id=user_id, category_id=category_id)
    if not category.is_archived:
        category.is_archived = True
        session.commit()
        session.refresh(category)
    return category
