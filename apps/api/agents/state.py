"""
RepoMedic — LangGraph Agent State

The RepoMedicState TypedDict defines all data flowing through the graph.
Nodes read from state and return partial dicts to update it.
"""

from __future__ import annotations

from typing import Any, TypedDict


class RepoMedicState(TypedDict, total=False):
    """
    Full agent state. Each key is set by a specific graph node.
    Keys are optional (total=False) since they accumulate through execution.
    """

    # -------------------------------------------------------------------------
    # Run identity
    # -------------------------------------------------------------------------
    run_id: str
    repository_full_name: str
    issue_number: int
    installation_id: int
    triggered_by: str

    # -------------------------------------------------------------------------
    # Repository info (set by repository_analysis node)
    # -------------------------------------------------------------------------
    repository: dict[str, Any]          # raw GitHub repo metadata
    repo_structure: list[str]           # file paths in the repo
    repo_snapshot_path: str             # local tmp path to repo clone/tarball
    default_branch: str

    # -------------------------------------------------------------------------
    # Issue (set by issue_analysis node)
    # -------------------------------------------------------------------------
    issue: dict[str, Any]               # raw GitHub issue data
    issue_analysis: dict[str, Any]      # IssueAnalysis Pydantic model dict

    # -------------------------------------------------------------------------
    # Code retrieval (set by code_retrieval node)
    # -------------------------------------------------------------------------
    retrieved_context: list[dict[str, Any]]  # list of CodeChunk dicts

    # -------------------------------------------------------------------------
    # Plan (set by planning node)
    # -------------------------------------------------------------------------
    plan: dict[str, Any]                # ImplementationPlan model dict

    # -------------------------------------------------------------------------
    # Patch (set by implementation / patch_revision nodes)
    # -------------------------------------------------------------------------
    current_patch: dict[str, Any]       # Patch model dict
    patch_history: list[dict[str, Any]] # all previous patches

    # -------------------------------------------------------------------------
    # Tests (set by test_generation node)
    # -------------------------------------------------------------------------
    generated_tests: list[dict[str, Any]]  # FileChange list for new/modified tests

    # -------------------------------------------------------------------------
    # Sandbox execution (set by sandbox_execution node)
    # -------------------------------------------------------------------------
    sandbox_run_id: str | None
    test_result: dict[str, Any] | None  # TestResult model dict

    # -------------------------------------------------------------------------
    # Failure analysis (set by failure_analysis node)
    # -------------------------------------------------------------------------
    failure_analysis: dict[str, Any] | None  # FailureAnalysis model dict

    # -------------------------------------------------------------------------
    # Web research (set by web_research node)
    # -------------------------------------------------------------------------
    research_results: list[dict[str, Any]]  # ResearchResult list

    # -------------------------------------------------------------------------
    # Iteration tracking
    # -------------------------------------------------------------------------
    iteration: int
    max_iterations: int

    # -------------------------------------------------------------------------
    # Patch review (set by verification node)
    # -------------------------------------------------------------------------
    patch_review: dict[str, Any] | None  # PatchReview model dict

    # -------------------------------------------------------------------------
    # PR creation (set by pr_generation node)
    # -------------------------------------------------------------------------
    pr_url: str | None
    pr_number: int | None
    branch_name: str | None

    # -------------------------------------------------------------------------
    # Terminal state
    # -------------------------------------------------------------------------
    status: str     # RUNNING | SUCCESS | FAILED | CANCELLED
    error: str | None
