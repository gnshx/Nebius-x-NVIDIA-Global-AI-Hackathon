"""
RepoMedic — Agent Node Base Utilities

Every node uses these helpers for:
- DB persistence (AgentStep create/update)
- SSE event emission via Redis pub/sub
- Structured logging with run context
"""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select

from config import settings
from db.database import AsyncSessionLocal
from models.orm import AgentRun, AgentStep, StepStatus, StepType

logger = structlog.get_logger(__name__)

# Redis client for SSE pub/sub
_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# ---------------------------------------------------------------------------
# SSE event emission
# ---------------------------------------------------------------------------

async def emit_event(run_id: str, event_type: str, data: dict[str, Any]) -> None:
    """Publish a run event to Redis for SSE consumers."""
    payload = json.dumps({
        "type": event_type,
        "run_id": run_id,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    redis = get_redis()
    await redis.publish(f"run:{run_id}", payload)


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
    return step_id


async def complete_step(
    step_id: str,
    status: StepStatus,
    output_metadata: dict[str, Any] | None = None,
    error: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Mark a step as complete/failed and store output."""
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


async def update_run_status(run_id: str, status: str) -> None:
    """Update the AgentRun status."""
    from models.orm import RunStatus
    async with AsyncSessionLocal() as session:
        run = await session.get(AgentRun, uuid.UUID(run_id))
        if run:
            run.status = RunStatus(status)
            if status in ("SUCCESS", "FAILED", "CANCELLED", "TIMED_OUT"):
                run.completed_at = datetime.now(timezone.utc)
            await session.commit()


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
