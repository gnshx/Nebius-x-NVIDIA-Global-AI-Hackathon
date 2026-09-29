"""
RepoMedic — Node: VERIFICATION

Performs a final structured review of the patch using the planner model.
Evaluates:
  - Correctness: does the change address the root cause?
  - Issue resolved: do the acceptance criteria appear satisfied?
  - Test adequacy: are the tests meaningful regressions?
  - Suspicious changes: any unexpected side effects?
  - Remaining risks: what could still go wrong?

Produces a `PatchReview` stored under `patch_review` in state.
The graph router will only proceed to pr_generation if review.correct AND
review.issue_resolved are True.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.orm import StepType
from models.schemas import PatchReview
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_MAX_DIFF_CHARS = 8_000


def _format_diff(current_patch: dict) -> str:
    """Format patch files into a readable diff block."""
    parts: list[str] = []
    for fc in current_patch.get("files", []):
        diff = (fc.get("patch", "") or "")[:_MAX_DIFF_CHARS // max(1, len(current_patch.get("files", [1])))]
        parts.append(
            f"### {fc.get('path', '')} [{fc.get('operation', '?')}]\n"
            f"Reason: {fc.get('reason', '')}\n"
            f"```diff\n{diff}\n```"
        )
    return "\n\n".join(parts)


async def run(state: RepoMedicState) -> dict:
    """Review the patch for correctness and issue resolution."""
    issue_analysis = state.get("issue_analysis") or {}
    current_patch = state.get("current_patch") or {}
    test_result = state.get("test_result") or {}
    plan = state.get("plan") or {}
    issue = state.get("issue") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.planner.model

    diff_str = _format_diff(current_patch)
    acceptance = "\n".join(
        f"  - {c}" for c in issue_analysis.get("acceptance_criteria", [])
    ) or "  (none specified)"
    test_summary = (
        f"Passed: {test_result.get('tests_passed')}, "
        f"Failed: {test_result.get('tests_failed')}, "
        f"Total: {test_result.get('tests_total')}"
    )

    messages = [
        Message(
            role="user",
            content=(
                "You are a senior code reviewer conducting a final quality gate review.\n\n"
                "## Issue\n"
                f"Title: {issue.get('title', '')}\n"
                f"Summary: {issue_analysis.get('summary', '')}\n"
                f"Problem: {issue_analysis.get('problem_statement', '')}\n"
                f"Expected: {issue_analysis.get('expected_behavior', '')}\n\n"
                "## Acceptance Criteria\n"
                f"{acceptance}\n\n"
                "## Root Cause Hypothesis\n"
                f"{plan.get('root_cause_hypothesis', '')}\n\n"
                "## Patch Applied\n"
                f"{diff_str}\n\n"
                "## Test Results\n"
                f"Success: {test_result.get('success', False)}\n"
                f"{test_summary}\n\n"
                "Review this patch. Flag any suspicious changes, incomplete fixes, "
                "or tests that do not adequately cover the regression scenario. "
                "Be strict: only approve if you are confident the issue is genuinely resolved."
            ),
        )
    ]

    logger.info("verification_start", run_id=run_id, iteration=iteration)

    async with node_context(
        run_id,
        StepType.VERIFICATION,
        iteration,
        model_used,
        {"iteration": iteration, "files_reviewed": len(current_patch.get("files", []))},
    ):
        review: PatchReview = await model_provider.planner.generate_structured(
            messages, PatchReview
        )

    logger.info(
        "verification_complete",
        run_id=run_id,
        correct=review.correct,
        issue_resolved=review.issue_resolved,
        tests_adequate=review.tests_adequate,
        summary=review.summary[:120],
    )

    return {"patch_review": review.model_dump()}
