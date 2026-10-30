"""
RepoMedic — Node: PATCH_REVISION

Uses the coder model to generate a revised patch that addresses the failure
identified by failure_analysis, optionally informed by web research results.

Security validation (PatchValidator) is re-applied on the new patch.
The revised patch replaces `current_patch` and is appended to `patch_history`.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.nodes.implementation import PatchValidator
from agents.state import RepoMedicState
from models.enums import StepType
from models.schemas import Patch
from services.nebius.client import Message, model_provider
from services.patch_minimizer import PatchMinimizer
from services.log_pruner import RuntimeLogPruner
from services.cross_validator import PatchCrossValidator
from services.sampling_adapter import DynamicSamplingAdapter

logger = structlog.get_logger(__name__)

_validator = PatchValidator()
_MAX_CHUNK_CHARS = 3_000


def _format_research(research_results: list[dict]) -> str:
    """Format web research results into a readable block."""
    if not research_results:
        return "(no web research available)"
    parts: list[str] = []
    for rr in research_results[-2:]:  # most recent two queries
        parts.append(f"Query: {rr.get('query', '')}")
        for r in (rr.get("results") or [])[:3]:
            parts.append(f"  [{r.get('title', '')}]({r.get('url', '')})")
            parts.append(f"  {r.get('content', '')[:400]}")
    return "\n".join(parts)


def _format_patch(patch: dict) -> str:
    """Show the current patch as a compact diff summary."""
    lines = [f"Summary: {patch.get('summary', '')}"]
    for fc in patch.get("files", []):
        diff_excerpt = (fc.get("patch", "") or "")[:600]
        lines.append(f"\n### {fc.get('path', '')} [{fc.get('operation', '?')}]")
        lines.append(f"Reason: {fc.get('reason', '')}")
        lines.append(f"```diff\n{diff_excerpt}\n```")
    return "\n".join(lines)


async def run(state: RepoMedicState) -> dict:
    """Generate a revised patch based on the failure analysis."""
    current_patch = state.get("current_patch") or {}
    test_result = state.get("test_result") or {}
    failure_analysis = state.get("failure_analysis") or {}
    research_results = state.get("research_results") or []
    plan = state.get("plan") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    patch_history: list[dict] = list(state.get("patch_history") or [])
    model_used = model_provider.coder.model

    patch_summary = _format_patch(current_patch)
    research_text = _format_research(research_results)
    # Isolate failure diagnostics using RuntimeLogPruner (SWE-Pruner)
    log_pruning = RuntimeLogPruner.prune_pytest_output(
        test_result.get("stdout", ""), test_result.get("stderr", ""), max_chars=3000
    )
    pruned_failure = log_pruning.pruned_text or test_result.get("failure_summary", "") or ""

    failing_tests_text = "\n".join(
        f"  - {t.get('name', '?')}: {t.get('error_type', '?')} — {t.get('message', '')}"
        for t in test_result.get("failing_tests", [])[:10]
    ) or "  (none parsed)"

    messages = [
        Message(
            role="system",
            content=(
                "You are an expert software engineer doing a targeted patch revision. "
                "The previous patch did not pass tests. Study the failure carefully and "
                "generate a corrected unified diff patch. Return a Patch object."
            ),
        ),
        Message(
            role="user",
            content=(
                "## Previous Patch\n"
                f"{patch_summary}\n\n"
                "## Test Failure\n"
                f"Category: {failure_analysis.get('category', 'UNKNOWN')}\n"
                f"Root cause: {failure_analysis.get('root_cause', '')}\n"
                f"Suggested fix: {failure_analysis.get('suggested_fix', '')}\n\n"
                "## Failing Tests\n"
                f"{failing_tests_text}\n\n"
                "## Pruned Diagnostic Failure Logs (SWE-Pruner)\n"
                f"{pruned_failure}\n\n"
                "## Web Research\n"
                f"{research_text}\n\n"
                "## Original Plan Root Cause\n"
                f"{plan.get('root_cause_hypothesis', '')}\n\n"
                f"This is revision attempt #{iteration}. "
                "Address ONLY the identified failure. Keep unrelated code unchanged. "
                "Generate a complete, valid unified diff for all files that need changing."
            ),
        ),
    ]

    # Evolutionary Test-Time Scaling (Satori-SWE EvoScale 2026)
    from services.evolutionary_patch_mutator import EvolutionaryPatchMutator
    mutator = EvolutionaryPatchMutator()
    prev_diff = "\n".join(fc.get("patch", "") for fc in current_patch.get("files", []))
    prev_candidate = mutator.evaluate_candidate(
        patch_id=f"iter_{iteration - 1}",
        diff_content=prev_diff,
        iteration=iteration - 1,
        tests_passed=test_result.get("tests_passed", 0),
        tests_total=test_result.get("tests_total", 0),
        syntax_valid=True,
        error_context=pruned_failure,
    )
    mutation_directives = mutator.formulate_mutation_prompt(
        prev_candidate, failure_analysis.get("suggested_fix", "")
    )
    messages[1].content += f"\n\n{mutation_directives}"

    # Calibrate dynamic sampling hyperparameters (TTC / SWE-Reasoner 2026)
    failure_delta = state.get("failure_delta") or {}
    delta_verdict = failure_delta.get("delta_verdict")
    sampling_config = DynamicSamplingAdapter.calibrate(
        iteration=iteration,
        delta_verdict=delta_verdict,
    )

    logger.info(
        "patch_revision_start",
        run_id=run_id,
        iteration=iteration,
        failure_category=failure_analysis.get("category"),
        sampling_mode=sampling_config.sampling_mode,
        temperature=sampling_config.temperature,
    )

    async with node_context(
        run_id,
        StepType.PATCH_REVISION,
        iteration,
        model_used,
        {
            "iteration": iteration,
            "failure_category": failure_analysis.get("category"),
            "sampling_config": sampling_config.to_dict(),
        },
    ):
        revised_patch: Patch = await model_provider.coder.generate_structured(
            messages, Patch
        )
        _validator.validate(revised_patch)
        revised_patch = PatchMinimizer.minimize(revised_patch)

    revised_dict = revised_patch.model_dump()
    patch_history.append(revised_dict)

    # Invariant cross-validation (TEX 2026)
    cross_val_report = PatchCrossValidator.validate_patch(revised_dict.get("files", []))

    logger.info(
        "patch_revision_complete",
        run_id=run_id,
        files_revised=len(revised_patch.files),
        invariant_score=cross_val_report.invariant_score,
        summary=revised_patch.summary[:120],
    )

    return {
        "current_patch": revised_dict,
        "patch_history": patch_history,
        "cross_validation": cross_val_report.to_dict(),
        "log_pruning": log_pruning.to_dict(),
        "sampling_config": sampling_config.to_dict(),
        "evolutionary_candidate": prev_candidate.to_dict(),
    }
