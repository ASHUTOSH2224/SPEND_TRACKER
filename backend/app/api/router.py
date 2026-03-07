from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.cards import router as cards_router
from app.api.routes.categories import router as categories_router
from app.api.routes.health import router as health_router
from app.api.routes.rules import router as rules_router
from app.api.routes.statements import router as statements_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(cards_router)
api_router.include_router(categories_router)
api_router.include_router(health_router)
api_router.include_router(rules_router)
api_router.include_router(statements_router)
api_router.include_router(transactions_router)
api_router.include_router(uploads_router)
