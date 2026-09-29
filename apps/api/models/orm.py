"""
RepoMedic — SQLAlchemy ORM Models

All tables use UUID primary keys and include created_at/updated_at timestamps.
JSONB is used for flexible metadata columns.
pgvector is used for code chunk embeddings.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class RunStatus(str, PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class StepStatus(str, PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class StepType(str, PyEnum):
    ISSUE_ANALYSIS = "issue_analysis"
    REPOSITORY_ANALYSIS = "repository_analysis"
    CODE_RETRIEVAL = "code_retrieval"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    TEST_GENERATION = "test_generation"
    SANDBOX_EXECUTION = "sandbox_execution"
    FAILURE_ANALYSIS = "failure_analysis"
    WEB_RESEARCH = "web_research"
    PATCH_REVISION = "patch_revision"
    VERIFICATION = "verification"
    PR_GENERATION = "pr_generation"


class RepositoryStatus(str, PyEnum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Mixin for common columns
# ---------------------------------------------------------------------------
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# github_installations
# ---------------------------------------------------------------------------
class GitHubInstallation(Base, TimestampMixin):
    __tablename__ = "github_installations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    installation_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    account_login: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # User | Organization
    suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    repositories: Mapped[list["Repository"]] = relationship(back_populates="installation")


# ---------------------------------------------------------------------------
# repositories
# ---------------------------------------------------------------------------
class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    installation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("github_installations.id", ondelete="SET NULL"), nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    language: Mapped[str | None] = mapped_column(String(100))
    private: Mapped[bool] = mapped_column(Boolean, default=False)
    index_status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus), default=RepositoryStatus.PENDING
    )
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    index_sha: Mapped[str | None] = mapped_column(String(40))  # Git SHA when last indexed

    installation: Mapped["GitHubInstallation | None"] = relationship(back_populates="repositories")
    issues: Mapped[list["Issue"]] = relationship(back_populates="repository")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="repository")
    code_chunks: Mapped[list["CodeChunk"]] = relationship(back_populates="repository")


# ---------------------------------------------------------------------------
# issues
# ---------------------------------------------------------------------------
class Issue(Base, TimestampMixin):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("repository_id", "number", name="uq_issue_repo_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), default="open")
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    labels: Mapped[list[str]] = mapped_column(JSONB, default=list)
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)

    repository: Mapped["Repository"] = relationship(back_populates="issues")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="issue")


# ---------------------------------------------------------------------------
# agent_runs
# ---------------------------------------------------------------------------
class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING, index=True)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    max_iterations: Mapped[int] = mapped_column(Integer, default=3)
    triggered_by: Mapped[str] = mapped_column(String(50), default="api")  # api | webhook | demo
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pr_url: Mapped[str | None] = mapped_column(String(500))
    pr_number: Mapped[int | None] = mapped_column(Integer)
    branch_name: Mapped[str | None] = mapped_column(String(255))
    error: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    repository: Mapped["Repository"] = relationship(back_populates="agent_runs")
    issue: Mapped["Issue | None"] = relationship(back_populates="agent_runs")
    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="run", order_by="AgentStep.created_at"
    )
    sandbox_runs: Mapped[list["SandboxRun"]] = relationship(back_populates="agent_run")
    pull_request: Mapped["PullRequest | None"] = relationship(back_populates="agent_run")


# ---------------------------------------------------------------------------
# agent_steps
# ---------------------------------------------------------------------------
class AgentStep(Base, TimestampMixin):
    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_type: Mapped[StepType] = mapped_column(Enum(StepType), nullable=False)
    status: Mapped[StepStatus] = mapped_column(Enum(StepStatus), default=StepStatus.PENDING)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    model_used: Mapped[str | None] = mapped_column(String(255))
    input_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

    run: Mapped["AgentRun"] = relationship(back_populates="steps")


# ---------------------------------------------------------------------------
# code_chunks  (pgvector)
# ---------------------------------------------------------------------------
class CodeChunk(Base, TimestampMixin):
    __tablename__ = "code_chunks"
    __table_args__ = (
        Index("ix_code_chunks_repo_path", "repository_id", "path"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="python")
    chunk_type: Mapped[str] = mapped_column(String(50))  # function | class | module | test
    symbol: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    imports: Mapped[list[str]] = mapped_column(JSONB, default=list)
    docstring: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[Any] = mapped_column(Vector(1024))  # BAAI/bge-en-icl dim

    repository: Mapped["Repository"] = relationship(back_populates="code_chunks")


# ---------------------------------------------------------------------------
# sandbox_runs
# ---------------------------------------------------------------------------
class SandboxRun(Base, TimestampMixin):
    __tablename__ = "sandbox_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sandbox_id: Mapped[str | None] = mapped_column(String(255))
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    timed_out: Mapped[bool] = mapped_column(Boolean, default=False)
    command: Mapped[str | None] = mapped_column(String(500))

    agent_run: Mapped["AgentRun"] = relationship(back_populates="sandbox_runs")
    test_result: Mapped["TestResult | None"] = relationship(back_populates="sandbox_run")


# ---------------------------------------------------------------------------
# test_results
# ---------------------------------------------------------------------------
class TestResult(Base, TimestampMixin):
    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sandbox_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sandbox_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tests_total: Mapped[int | None] = mapped_column(Integer)
    tests_passed: Mapped[int | None] = mapped_column(Integer)
    tests_failed: Mapped[int | None] = mapped_column(Integer)
    tests_skipped: Mapped[int | None] = mapped_column(Integer)
    failure_summary: Mapped[str | None] = mapped_column(Text)
    failing_tests: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    raw_output: Mapped[str | None] = mapped_column(Text)

    sandbox_run: Mapped["SandboxRun"] = relationship(back_populates="test_result")


# ---------------------------------------------------------------------------
# research_queries  (Tavily)
# ---------------------------------------------------------------------------
class ResearchQuery(Base, TimestampMixin):
    __tablename__ = "research_queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    results: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    selected_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)


# ---------------------------------------------------------------------------
# pull_requests
# ---------------------------------------------------------------------------
class PullRequest(Base, TimestampMixin):
    __tablename__ = "pull_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    merged: Mapped[bool] = mapped_column(Boolean, default=False)

    agent_run: Mapped["AgentRun"] = relationship(back_populates="pull_request")
