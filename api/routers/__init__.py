"""
Main API router that combines all specialized routers
"""
from fastapi import APIRouter
from api.routers.settings import router as settings_router
from api.routers.documents import router as documents_router
from api.routers.query import router as query_router
from api.routers.sessions import router as sessions_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(query_router, prefix="/query", tags=["query"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])