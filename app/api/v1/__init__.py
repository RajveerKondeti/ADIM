from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.auth import router as auth_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent"])
api_router.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])