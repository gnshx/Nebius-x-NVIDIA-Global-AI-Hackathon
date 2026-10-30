"""
RepoMedic — Node: FAILURE_ANALYSIS

Uses the fast model to classify a test failure and determine whether web
research is required before attempting a patch revision.

Failure categories (from FailureAnalysis schema):
- CODE_ERROR      → logic/assertion error, is_actionable=True
- TEST_ERROR      → test itself is wrong (unlikely here)
- DEPENDENCY_ERROR→ missing/incompatible library, requires_research=True
- ENVIRONMENT_ERROR → sandbox config problem, is_actionable=False
- TIMEOUT         → test run exceeded limit, is_actionable=False
- UNKNOWN         → catch-all, requires_research=True

The node pre-classifies based on stderr heuristics to give the model a hint.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.enums import StepType
from models.schemas import FailureAnalysis, FailureCategory
from services.nebius.client import Message, model_provider
from services.log_pruner import RuntimeLogPruner
from services.failure_distiller import FailureDistiller

logger = structlog.get_logger(__name__)


def _preClassify(stdout: str, stderr: str) -> FailureCategory | None:
    """Lightweight heuristic pre-classification from raw output."""
    combined = (stderr + "\n" + stdout).lower()
    if "syntaxerror" in combined:
        return FailureCategory.CODE_ERROR
    if "assertionerror" in combined or "assert" in combined:
        return FailureCategory.CODE_ERROR
    if "importerror" in combined or "modulenotfounderror" in combined:
        return FailureCategory.DEPENDENCY_ERROR
    if "timeouterror" in combined or "timed out" in combined:
        return FailureCategory.TIMEOUT
    return None


async def run(state: RepoMedicState) -> dict:
    """Classify the test failure and decide whether research is needed."""
    test_result = state.get("test_result") or {}
    current_patch = state.get("current_patch") or {}
    plan = state.get("plan") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.fast.model

    stdout: str = test_result.get("stdout", "")
    stderr: str = test_result.get("stderr", "")
    failure_summary: str = test_result.get("failure_summary", "") or ""
    failing_tests: list[dict] = test_result.get("failing_tests", [])

    # Apply task-aware log pruning (SWE-Pruner) to isolate failure stacktraces
    log_pruning = RuntimeLogPruner.prune_pytest_output(stdout, stderr, max_chars=3000)
    pruned_failure_text = log_pruning.pruned_text or failure_summary

    # Compute differential failure delta across multi-turn iterations (SWE-bench 2026)
    previous_failing_tests = state.get("previous_failing_tests") or []
    failure_delta = FailureDistiller.distill_delta(previous_failing_tests, failing_tests)

    # Build a failing-tests summary for the prompt
    ft_text = "\n".join(
        f"  - {t.get('name', '?')}: {t.get('error_type', '?')} — {t.get('message', '')}"
        for t in failing_tests[:10]
    ) or "  (none parsed)"

    patch_summary = "\n".join(
        f"  [{f.get('operation', '?')}] {f.get('path', '?')}"
        for f in current_patch.get("files", [])
    )

    hint = f"Pre-classification hint: {pre_class.value}" if pre_class else ""

    messages = [
        Message(
            role="user",
            content=(
                "Analyze this test failure from an automated fix attempt.\n\n"
                f"## Multi-Turn Failure Delta (Self-Healing)\n{failure_delta.diagnostic_prompt}\n\n"
                f"## Pruned Diagnostic Failure Logs (SWE-Pruner)\n{pruned_failure_text}\n\n"
                f"## Current Failing Tests\n{ft_text}\n\n"
                f"## Patch Applied\n{patch_summary}\n\n"
                f"## Plan Root Cause\n{plan.get('root_cause_hypothesis', '')}\n\n"
                f"{hint}\n\n"
                "Classify the failure, identify root cause, and decide whether "
                "web research is needed. If research is needed, provide a precise query."
            ),
        )
    ]

    logger.info(
        "failure_analysis_start",
        run_id=run_id,
        iteration=iteration,
        pre_class=pre_class.value if pre_class else None,
        failing_tests=len(failing_tests),
        delta_verdict=failure_delta.delta_verdict,
    )

    async with node_context(
        run_id,
        StepType.FAILURE_ANALYSIS,
        iteration,
        model_used,
        {"iteration": iteration, "failing_tests": len(failing_tests)},
    ):
        analysis: FailureAnalysis = await model_provider.fast.generate_structured(
            messages, FailureAnalysis
        )

    logger.info(
        "failure_analysis_complete",
        run_id=run_id,
        category=analysis.category.value,
        is_actionable=analysis.is_actionable,
        requires_research=analysis.requires_research,
        root_cause=analysis.root_cause[:120],
    )

    return {
        "failure_analysis": analysis.model_dump(),
        "log_pruning": log_pruning.to_dict(),
        "failure_delta": failure_delta.to_dict(),
        "previous_failing_tests": failing_tests,
    }
