"""RepoMedic — Agent Runs Routes"""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from celery_app import start_agent_run_task
from db.database import get_db
from models.orm import AgentRun, Repository, RunStatus
from models.schemas import AgentRunResponse, RunCreate, RunListResponse

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreate, db: DbDep) -> AgentRunResponse:
    """
    Trigger a new RepoMedic agent run for a GitHub issue.
    Idempotency: rejects if an active run already exists for this issue.
    """
    # 1. Find repository
    result = await db.execute(
        select(Repository).where(Repository.full_name == payload.repository_full_name)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{payload.repository_full_name}' not registered. Add it first.",
        )

    # 2. Idempotency check — no active run for same issue
    active_result = await db.execute(
        select(AgentRun).where(
            AgentRun.repository_id == repo.id,
            AgentRun.issue_number == payload.issue_number,
            AgentRun.status.in_([RunStatus.PENDING, RunStatus.RUNNING]),
        )
    )
    existing_active = active_result.scalar_one_or_none()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active run already exists for issue #{payload.issue_number}",
        )

    # 3. Create the run record
    run = AgentRun(
        id=uuid.uuid4(),
        repository_id=repo.id,
        issue_number=payload.issue_number,
        status=RunStatus.PENDING,
        max_iterations=payload.max_iterations,
        triggered_by="api",
    )
    db.add(run)
    await db.flush()

    run_id = str(run.id)
    logger.info("run_created", run_id=run_id, repo=payload.repository_full_name, issue=payload.issue_number)

    # 4. Dispatch Celery task
    task = start_agent_run_task.delay(
        repository_full_name=payload.repository_full_name,
        issue_number=payload.issue_number,
        installation_id=repo.installation_id or 0,
        triggered_by="api",
        run_id=run_id,
    )
    run.celery_task_id = task.id
    await db.commit()
    await db.refresh(run)

    return AgentRunResponse.model_validate(run)


@router.get("", response_model=RunListResponse)
async def list_runs(
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    repository: str | None = Query(default=None),
) -> RunListResponse:
    """List all agent runs with pagination."""
    query = select(AgentRun).order_by(AgentRun.created_at.desc())

    if status:
        try:
            run_status = RunStatus(status.upper())
            query = query.where(AgentRun.status == run_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if repository:
        repo_result = await db.execute(
            select(Repository).where(Repository.full_name == repository)
        )
        repo = repo_result.scalar_one_or_none()
        if repo:
            query = query.where(AgentRun.repository_id == repo.id)

    # Count total
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    runs = result.scalars().all()

    return RunListResponse(
        runs=[AgentRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: str, db: DbDep) -> AgentRunResponse:
    """Get a specific agent run with all steps."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    result = await db.execute(
        select(AgentRun)
        .options(selectinload(AgentRun.steps))
        .where(AgentRun.id == run_uuid)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return AgentRunResponse.model_validate(run)


@router.post("/{run_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_run(run_id: str, db: DbDep) -> dict:
    """Cancel a running agent run."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    result = await db.execute(select(AgentRun).where(AgentRun.id == run_uuid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if run.status not in (RunStatus.PENDING, RunStatus.RUNNING):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel run in status {run.status.value}",
        )

    # Revoke Celery task
    if run.celery_task_id:
        from celery_app import celery
        celery.control.revoke(run.celery_task_id, terminate=True, signal="SIGTERM")

    run.status = RunStatus.CANCELLED
    await db.commit()

    logger.info("run_cancelled", run_id=run_id)
    return {"run_id": run_id, "status": "CANCELLED"}
