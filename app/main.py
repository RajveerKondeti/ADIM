"""
main.py — application entry point.

Run with:
    uvicorn app.main:app --reload              # development
    uvicorn app.main:app --workers 4           # production (no --reload)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.db.init_db import init_db

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    yield
    # Shutdown — add cleanup here (close Redis, Kafka producer, etc.)
    logger.info("👋 Shutting down ADIM.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Decision Intelligence Mesh — AI-native operational brain.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Tighten origins in production — don't use ["*"] in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Kubernetes/load-balancer liveness probe endpoint."""
    return {"status": "ok", "version": settings.APP_VERSION}