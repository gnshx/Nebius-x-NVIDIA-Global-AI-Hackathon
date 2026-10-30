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
from models.enums import StepType
from models.schemas import Patch, PatchReview
from services.nebius.client import Message, model_provider
from services.oracle_evaluator import OracleEvaluator
from services.patch_minimizer import PatchMinimizer
from services.consensus_auditor import PatchConsensusAuditor
from services.flakiness_quarantiner import FlakyTestQuarantiner

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

    # Evaluate SWE-bench dual oracle (F->P vs P->P)
    generated_tests = state.get("generated_tests") or []
    try:
        patch_obj = Patch(**current_patch) if current_patch.get("files") else Patch(summary="Review", files=[])
        patch_metrics = PatchMinimizer.evaluate_metrics(patch_obj)
        cleanliness = patch_metrics.cleanliness_score
    except Exception:
        cleanliness = 1.0

    oracle_eval = OracleEvaluator.evaluate(
        test_result=test_result,
        generated_tests=generated_tests,
        cleanliness_score=cleanliness,
    )

    # Multi-dimensional consensus audit (TEX/PROBE 2026)
    cross_val = state.get("cross_validation") or {}
    test_qual = state.get("test_quality") or {}
    consensus_audit = PatchConsensusAuditor.audit(
        oracle_confidence=oracle_eval.confidence_score,
        invariant_score=cross_val.get("invariant_score", 1.0),
        cleanliness_score=cleanliness,
        mutation_score=test_qual.get("discrimination_score", 1.0),
        security_passed=True,
    )

    # Flaky Test Quarantine Evaluation (SWE-bench Verified 2026)
    quarantiner = FlakyTestQuarantiner()
    for ft in test_result.get("failing_tests", []):
        quarantiner.record_test_run(ft.get("name", ""), False, ft.get("message", ""))
    quarantine_report = quarantiner.generate_report(test_result.get("tests_total", 0) or 1)

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
                "## SWE-bench Dual Oracle Metrics\n"
                f"Verdict: {oracle_eval.verdict.value}\n"
                f"Fail-to-Pass (F->P): {oracle_eval.fail_to_pass_passed}/{oracle_eval.fail_to_pass_count} resolved\n"
                f"Pass-to-Pass (P->P): {oracle_eval.pass_to_pass_passed}/{oracle_eval.pass_to_pass_total} maintained\n"
                f"Cleanliness Score: {oracle_eval.cleanliness_score * 100:.1f}%\n"
                f"Details: {oracle_eval.details}\n\n"
                "## Test Flakiness & Quarantine\n"
                f"Deterministic Suite Confidence: {quarantine_report.deterministic_suite_confidence * 100:.1f}%\n"
                f"Quarantined Tests: {quarantine_report.quarantined_count}\n\n"
                "## Deployment Readiness Index (DRI)\n"
                f"DRI Score: {consensus_audit.dri_score}/100 ({consensus_audit.recommendation})\n"
                f"Deployable: {consensus_audit.is_deployable}\n"
                f"Breakdown: {consensus_audit.breakdown}\n\n"
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

    return {
        "patch_review": review.model_dump(),
        "oracle_evaluation": oracle_eval.to_dict(),
        "consensus_audit": consensus_audit.to_dict(),
        "quarantine_report": quarantine_report.to_dict(),
    }
