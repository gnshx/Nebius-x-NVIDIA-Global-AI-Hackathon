"""
RepoMedic — Agent Node Base Utilities

Provides:
- Step lifecycle tracking & execution context manager (node_context)
- Event emission via Redis pub/sub (with in-memory fallback)
- DB persistence (AgentStep create/update, with offline resilience)
- Secret redaction for audit logs
"""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import structlog

from config import settings
from models.enums import StepStatus, StepType

logger = structlog.get_logger(__name__)

# Redis client for SSE pub/sub
_redis: Any = None
_redis_available: bool | None = None


def get_redis() -> Any:
    global _redis, _redis_available
    if _redis_available is False:
        return None
    if _redis is None:
        try:
            import redis.asyncio as aioredis
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            _redis_available = True
        except Exception:
            _redis_available = False
            return None
    return _redis


# ---------------------------------------------------------------------------
# SSE event emission
# ---------------------------------------------------------------------------

async def emit_event(run_id: str, event_type: str, data: dict[str, Any]) -> None:
    """Publish a run event to Redis for SSE consumers (or log fallback)."""
    payload = json.dumps({
        "type": event_type,
        "run_id": run_id,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    try:
        redis = get_redis()
        if redis:
            await redis.publish(f"run:{run_id}", payload)
        else:
            logger.debug("event_emitted_offline", run_id=run_id, type=event_type)
    except Exception as e:
        logger.debug("redis_publish_skipped", error=str(e))


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def create_step(
    run_id: str,
    step_type: StepType,
    iteration: int = 0,
    model_used: str | None = None,
    input_metadata: dict[str, Any] | None = None,
) -> str:
    """Create a new AgentStep row and return its ID."""
    step_id = str(uuid.uuid4())
    try:
        from db.database import AsyncSessionLocal
        from models.orm import AgentStep

        async with AsyncSessionLocal() as session:
            step = AgentStep(
                id=uuid.UUID(step_id),
                run_id=uuid.UUID(run_id),
                step_type=step_type,
                status=StepStatus.RUNNING,
                iteration=iteration,
                started_at=datetime.now(timezone.utc),
                model_used=model_used,
                input_metadata=input_metadata or {},
            )
            session.add(step)
            await session.commit()
    except Exception as db_exc:
        logger.debug("create_step_db_skipped", error=str(db_exc))
    return step_id


async def complete_step(
    step_id: str,
    status: StepStatus,
    output_metadata: dict[str, Any] | None = None,
    error: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Mark a step as complete/failed and store output."""
    try:
        from db.database import AsyncSessionLocal
        from models.orm import AgentStep

        async with AsyncSessionLocal() as session:
            step = await session.get(AgentStep, uuid.UUID(step_id))
            if step:
                step.status = status
                step.completed_at = datetime.now(timezone.utc)
                step.output_metadata = output_metadata or {}
                step.error = error
                if duration_seconds is not None:
                    step.duration_seconds = duration_seconds
                elif step.started_at:
                    delta = datetime.now(timezone.utc) - step.started_at
                    step.duration_seconds = delta.total_seconds()
                await session.commit()
    except Exception as db_exc:
        logger.debug("complete_step_db_skipped", error=str(db_exc))


async def update_run_status(run_id: str, status: str) -> None:
    """Update the AgentRun status."""
    try:
        from db.database import AsyncSessionLocal
        from models.orm import AgentRun, RunStatus

        async with AsyncSessionLocal() as session:
            run = await session.get(AgentRun, uuid.UUID(run_id))
            if run:
                run.status = RunStatus(status)
                if status in ("SUCCESS", "FAILED", "CANCELLED", "TIMED_OUT"):
                    run.completed_at = datetime.now(timezone.utc)
                await session.commit()
    except Exception as db_exc:
        logger.debug("update_run_status_db_skipped", error=str(db_exc))


# ---------------------------------------------------------------------------
# Node context manager — wraps a node execution with DB + SSE lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def node_context(
    run_id: str,
    step_type: StepType,
    iteration: int = 0,
    model_used: str | None = None,
    input_summary: dict[str, Any] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Context manager that:
    1. Creates AgentStep in DB (RUNNING)
    2. Emits step_started SSE event
    3. On exit: marks step SUCCESS/FAILED, emits step_completed/step_failed
    """
    step_id = await create_step(
        run_id=run_id,
        step_type=step_type,
        iteration=iteration,
        model_used=model_used,
        input_metadata=input_summary,
    )
    await emit_event(run_id, "step_started", {
        "step_type": step_type.value,
        "step_id": step_id,
        "iteration": iteration,
    })
    try:
        yield step_id
        await complete_step(step_id, StepStatus.SUCCESS)
        await emit_event(run_id, "step_completed", {
            "step_type": step_type.value,
            "step_id": step_id,
        })
    except Exception as exc:
        await complete_step(
            step_id,
            StepStatus.FAILED,
            error=str(exc),
        )
        await emit_event(run_id, "step_failed", {
            "step_type": step_type.value,
            "step_id": step_id,
            "error": str(exc),
        })
        raise


# ---------------------------------------------------------------------------
# Secret redaction — never log credentials
# ---------------------------------------------------------------------------

_REDACTED_KEYS = frozenset({
    "api_key", "private_key", "token", "password", "secret",
    "webhook_secret", "nebius_api_key", "tavily_api_key",
    "github_private_key", "access_token", "installation_token",
})


def redact_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive keys before storing to agent_steps metadata."""
    return {
        k: "[REDACTED]" if k.lower() in _REDACTED_KEYS else v
        for k, v in data.items()
    }
