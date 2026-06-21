from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, residences, tasks, events, messages

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(residences.router, tags=["Residences & Residents"])
api_router.include_router(tasks.router, tags=["Tasks & Chores"])
api_router.include_router(events.router, tags=["Events & Calendar"])
api_router.include_router(messages.router, tags=["Mural & Messages"])



