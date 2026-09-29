"""
RepoMedic — Celery Application

Background task queue for agent runs.
Workers pick up agent runs from the Redis queue and execute the LangGraph graph.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from celery import Celery
from celery.signals import task_failure, task_prerun, task_success

from config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Celery app
# ---------------------------------------------------------------------------
celery = Celery(
    "repomedic",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["celery_app"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # one task at a time per worker
    task_routes={
        "celery_app.start_agent_run_task": {"queue": "agent_runs"},
    },
)


# ---------------------------------------------------------------------------
# Agent run task
# ---------------------------------------------------------------------------

@celery.task(
    bind=True,
    name="celery_app.start_agent_run_task",
    max_retries=0,      # Agent handles its own retry loop; Celery doesn't retry
    time_limit=1800,    # 30 min hard timeout
    soft_time_limit=1500,
)
def start_agent_run_task(
    self: Any,
    repository_full_name: str,
    issue_number: int,
    installation_id: int,
    triggered_by: str = "api",
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Celery task that executes a RepoMedic agent run.
    Runs the LangGraph graph synchronously in a new event loop.
    """
    run_id = run_id or str(uuid.uuid4())
    logger.info(
        "agent_run_started",
        run_id=run_id,
        repo=repository_full_name,
        issue=issue_number,
        triggered_by=triggered_by,
    )

    # Update Celery task ID on the run
    asyncio.run(_run_agent(
        run_id=run_id,
        repository_full_name=repository_full_name,
        issue_number=issue_number,
        installation_id=installation_id,
        triggered_by=triggered_by,
        celery_task_id=self.request.id,
    ))

    return {"run_id": run_id, "status": "completed"}


async def _run_agent(
    run_id: str,
    repository_full_name: str,
    issue_number: int,
    installation_id: int,
    triggered_by: str,
    celery_task_id: str,
) -> None:
    """
    Initialize the DB run record and execute the LangGraph graph.
    """
    from db.database import AsyncSessionLocal
    from models.orm import AgentRun, RunStatus

    # 1. Ensure the AgentRun exists in DB (may have been created by API)
    async with AsyncSessionLocal() as session:
        existing = await session.get(AgentRun, uuid.UUID(run_id))
        if not existing:
            # Created by webhook — look up or create repo + issue
            # Simplified: just log; full impl creates repo/issue records
            logger.warning("run_not_found_in_db_creating", run_id=run_id)

        # Update status to RUNNING
        if existing:
            existing.status = RunStatus.RUNNING
            existing.started_at = datetime.now(timezone.utc)
            existing.celery_task_id = celery_task_id
            await session.commit()

    # 2. Build initial state
    initial_state = {
        "run_id": run_id,
        "repository_full_name": repository_full_name,
        "issue_number": issue_number,
        "installation_id": installation_id,
        "triggered_by": triggered_by,
        "iteration": 0,
        "max_iterations": settings.max_fix_iterations,
        "status": "RUNNING",
        "research_results": [],
        "patch_history": [],
        "retrieved_context": [],
        "generated_tests": [],
    }

    # 3. Execute the graph
    from agents.graph import repomedic_graph
    try:
        final_state = await repomedic_graph.ainvoke(initial_state)
        logger.info(
            "agent_run_finished",
            run_id=run_id,
            status=final_state.get("status"),
            pr_url=final_state.get("pr_url"),
            iterations=final_state.get("iteration"),
        )
    except Exception as exc:
        logger.error("agent_run_exception", run_id=run_id, error=str(exc), exc_info=True)
        async with AsyncSessionLocal() as session:
            run = await session.get(AgentRun, uuid.UUID(run_id))
            if run:
                run.status = RunStatus.FAILED
                run.error = str(exc)
                run.completed_at = datetime.now(timezone.utc)
                await session.commit()
        raise
