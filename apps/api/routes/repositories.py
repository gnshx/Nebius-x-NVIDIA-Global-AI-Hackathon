"""RepoMedic — Repositories Routes"""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.orm import Repository, RepositoryStatus
from models.schemas import RepositoryCreate, RepositoryResponse

router = APIRouter()
logger = structlog.get_logger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def register_repository(payload: RepositoryCreate, db: DbDep) -> RepositoryResponse:
    """Register a new repository for RepoMedic to monitor."""
    # Check for duplicate
    result = await db.execute(
        select(Repository).where(Repository.full_name == payload.full_name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return RepositoryResponse.model_validate(existing)

    owner, name = payload.full_name.split("/", 1)
    repo = Repository(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        owner=owner,
        name=name,
        index_status=RepositoryStatus.PENDING,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    logger.info("repository_registered", repo=payload.full_name)
    return RepositoryResponse.model_validate(repo)


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(db: DbDep) -> list[RepositoryResponse]:
    """List all registered repositories."""
    result = await db.execute(select(Repository).order_by(Repository.created_at.desc()))
    repos = result.scalars().all()
    return [RepositoryResponse.model_validate(r) for r in repos]


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: DbDep) -> RepositoryResponse:
    """Get a specific repository by ID or full_name."""
    # Try UUID first
    try:
        repo_uuid = uuid.UUID(repo_id)
        result = await db.execute(select(Repository).where(Repository.id == repo_uuid))
    except ValueError:
        # Try full_name (URL-encoded slash would be %2F but FastAPI handles it)
        result = await db.execute(
            select(Repository).where(Repository.full_name == repo_id)
        )

    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found")

    return RepositoryResponse.model_validate(repo)
