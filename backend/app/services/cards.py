from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.card import Card
from app.schemas.cards import CardCreate, CardUpdate


def list_cards_for_user(session: Session, *, user_id: UUID) -> list[Card]:
    statement = (
        select(Card)
        .where(Card.user_id == user_id)
        .order_by(
            case((Card.status == "active", 0), else_=1),
            Card.created_at.desc(),
        )
    )
    return list(session.scalars(statement).all())


def create_card_for_user(
    session: Session,
    *,
    user_id: UUID,
    payload: CardCreate,
) -> Card:
    card = Card(
        user_id=user_id,
        **payload.model_dump(),
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def get_card_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> Card:
    statement = select(Card).where(
        Card.id == card_id,
        Card.user_id == user_id,
    )
    card = session.scalar(statement)
    if card is None:
        raise AppException(
            status_code=404,
            code="CARD_NOT_FOUND",
            message="Card not found",
        )
    return card


def update_card_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
    payload: CardUpdate,
) -> Card:
    card = get_card_for_user(session, user_id=user_id, card_id=card_id)
    updates = payload.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        setattr(card, field_name, value)

    session.commit()
    session.refresh(card)
    return card


def archive_card_for_user(
    session: Session,
    *,
    user_id: UUID,
    card_id: UUID,
) -> Card:
    card = get_card_for_user(session, user_id=user_id, card_id=card_id)
    if card.status != "archived":
        card.status = "archived"
        session.commit()
        session.refresh(card)
    return card
