"""API v1 router registry."""

from fastapi import APIRouter

from app.api.v1.sessions import router as sessions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(sessions_router)
