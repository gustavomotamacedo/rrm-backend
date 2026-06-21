from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, residences

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(residences.router, tags=["Residences & Residents"])


