"""
RepoMedic — Pydantic API Schemas

These are the request/response models for the REST API.
Keep them separate from SQLAlchemy ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


from models.enums import RepositoryStatus, RunStatus, StepStatus, StepType


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------
class RepositoryCreate(BaseModel):
    full_name: str = Field(..., pattern=r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
    installation_id: int | None = None


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    owner: str
    name: str
    default_branch: str
    language: str | None
    private: bool
    index_status: str
    last_indexed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent Run
# ---------------------------------------------------------------------------
class RunCreate(BaseModel):
    repository_full_name: str = Field(..., pattern=r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
    issue_number: int = Field(..., gt=0)
    max_iterations: int = Field(default=3, ge=1, le=10)


class AgentStepResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    step_type: StepType
    status: StepStatus
    iteration: int
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    model_used: str | None
    input_metadata: dict[str, Any]
    output_metadata: dict[str, Any]
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRunResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    issue_number: int
    status: RunStatus
    iteration: int
    max_iterations: int
    triggered_by: str
    started_at: datetime | None
    completed_at: datetime | None
    pr_url: str | None
    pr_number: int | None
    branch_name: str | None
    error: str | None
    steps: list[AgentStepResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    runs: list[AgentRunResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Test Result
# ---------------------------------------------------------------------------
class FailingTestSchema(BaseModel):
    name: str
    error_type: str
    message: str
    traceback: str


class TestResultSchema(BaseModel):
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    tests_total: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    tests_skipped: int | None = None
    failure_summary: str | None = None
    failing_tests: list[FailingTestSchema] = []


# ---------------------------------------------------------------------------
# Issue Analysis (LLM output)
# ---------------------------------------------------------------------------
class IssueAnalysis(BaseModel):
    summary: str
    problem_statement: str
    expected_behavior: str
    observed_behavior: str
    likely_components: list[str]
    relevant_files: list[str]
    acceptance_criteria: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Implementation Plan (LLM output)
# ---------------------------------------------------------------------------
class ImplementationPlan(BaseModel):
    root_cause_hypothesis: str
    files_to_modify: list[str]
    files_to_add: list[str]
    tests_to_modify: list[str]
    tests_to_add: list[str]
    changes: list[str]
    risks: list[str]
    verification_strategy: list[str]
    test_command: str = "pytest"


# ---------------------------------------------------------------------------
# Patch / File Changes
# ---------------------------------------------------------------------------
class FileChange(BaseModel):
    path: str
    operation: str  # modify | create | delete
    patch: str      # unified diff
    reason: str


class Patch(BaseModel):
    files: list[FileChange]
    summary: str
    test_command: str = "pytest"


# ---------------------------------------------------------------------------
# Failure Analysis
# ---------------------------------------------------------------------------
class FailureCategory(str, Enum):
    CODE_ERROR = "CODE_ERROR"
    TEST_ERROR = "TEST_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class FailureAnalysis(BaseModel):
    category: FailureCategory
    is_actionable: bool
    root_cause: str
    requires_research: bool
    research_query: str | None = None
    suggested_fix: str


# ---------------------------------------------------------------------------
# Patch Review
# ---------------------------------------------------------------------------
class PatchReview(BaseModel):
    correct: bool
    issue_resolved: bool
    tests_adequate: bool
    suspicious_changes: list[str]
    remaining_risks: list[str]
    summary: str


# ---------------------------------------------------------------------------
# SSE Event
# ---------------------------------------------------------------------------
class RunEvent(BaseModel):
    type: str
    run_id: str
    data: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
