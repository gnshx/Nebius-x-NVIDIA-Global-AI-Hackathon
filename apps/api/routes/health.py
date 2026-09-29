"""RepoMedic — Health Check Route"""
from __future__ import annotations

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from db.database import AsyncSessionLocal
from models.schemas import HealthResponse
from config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint. Verifies DB and Redis connectivity."""
    db_status = "ok"
    redis_status = "ok"

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"
        logger.error("health_db_error", error=str(e))

    try:
        from agents.nodes.base import get_redis
        redis = get_redis()
        await redis.ping()
    except Exception as e:
        redis_status = f"error: {e}"
        logger.error("health_redis_error", error=str(e))

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        environment=settings.app_env.value,
        database=db_status,
        redis=redis_status,
    )
