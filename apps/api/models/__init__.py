"""
RepoMedic Models Package.
Exports ORM models, Pydantic schemas, and core Enums.
"""

from .enums import RepositoryStatus, RunStatus, StepStatus, StepType

try:
    from .orm import (
        GitHubInstallation,
        Repository,
        Issue,
        AgentRun,
        AgentStep,
        CodeChunk,
        SandboxRun,
        TestResult,
        ResearchQuery,
        PullRequest,
    )
except ImportError:
    # Running outside DB container without sqlalchemy
    GitHubInstallation = Repository = Issue = AgentRun = AgentStep = None  # type: ignore
    CodeChunk = SandboxRun = TestResult = ResearchQuery = PullRequest = None  # type: ignore

from .schemas import (
    RepositoryCreate,
    RepositoryResponse,
    RunCreate,
    AgentRunResponse,
    AgentStepResponse,
    RunListResponse,
    TestResultSchema,
    IssueAnalysis,
    ImplementationPlan,
    FileChange,
    Patch,
    FailureAnalysis,
    PatchReview,
    RunEvent,
    HealthResponse,
)

__all__ = [
    # Enums
    "RunStatus",
    "StepStatus",
    "StepType",
    "RepositoryStatus",
    # ORM models
    "GitHubInstallation",
    "Repository",
    "Issue",
    "AgentRun",
    "AgentStep",
    "CodeChunk",
    "SandboxRun",
    "TestResult",
    "ResearchQuery",
    "PullRequest",
    # Schemas
    "RepositoryCreate",
    "RepositoryResponse",
    "RunCreate",
    "AgentRunResponse",
    "AgentStepResponse",
    "RunListResponse",
    "TestResultSchema",
    "IssueAnalysis",
    "ImplementationPlan",
    "FileChange",
    "Patch",
    "FailureAnalysis",
    "PatchReview",
    "RunEvent",
    "HealthResponse",
]
