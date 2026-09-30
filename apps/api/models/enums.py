"""
RepoMedic — Shared Core Enums

Standard library enums with zero external dependencies (no sqlalchemy/pgvector).
Used across ORM, schemas, agents, and state.
"""

from __future__ import annotations

from enum import Enum


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class StepType(str, Enum):
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


class RepositoryStatus(str, Enum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
