from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.cards import CardCreate, CardRead, CardUpdate
from app.schemas.common import ResponseEnvelope, success_response
from app.services.cards import (
    archive_card_for_user,
    create_card_for_user,
    get_card_for_user,
    list_cards_for_user,
    update_card_for_user,
)

router = APIRouter(prefix="/cards", tags=["cards"])


def _serialize_card(card) -> CardRead:
    return CardRead.model_validate(card)


@router.get("", response_model=ResponseEnvelope[list[CardRead]], status_code=status.HTTP_200_OK)
def list_cards(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[CardRead]]:
    cards = list_cards_for_user(session, user_id=current_user.id)
    return success_response([_serialize_card(card) for card in cards])


@router.post("", response_model=ResponseEnvelope[CardRead], status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = create_card_for_user(
        session,
        user_id=current_user.id,
        payload=payload,
    )
    return success_response(_serialize_card(card))


@router.get(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def get_card(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = get_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(_serialize_card(card))


@router.patch(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def update_card(
    card_id: UUID,
    payload: CardUpdate,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = update_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
        payload=payload,
    )
    return success_response(_serialize_card(card))


@router.delete(
    "/{card_id}",
    response_model=ResponseEnvelope[CardRead],
    status_code=status.HTTP_200_OK,
)
def archive_card(
    card_id: UUID,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CardRead]:
    card = archive_card_for_user(
        session,
        user_id=current_user.id,
        card_id=card_id,
    )
    return success_response(_serialize_card(card))
