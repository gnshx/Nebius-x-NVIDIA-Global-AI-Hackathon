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
from models.orm import StepType
from models.schemas import Patch
from services.nebius.client import Message, model_provider

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
    failure_summary = test_result.get("failure_summary", "") or ""
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
                "## Failure Output (last 30 lines)\n"
                f"{failure_summary}\n\n"
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

    logger.info(
        "patch_revision_start",
        run_id=run_id,
        iteration=iteration,
        failure_category=failure_analysis.get("category"),
    )

    async with node_context(
        run_id,
        StepType.PATCH_REVISION,
        iteration,
        model_used,
        {"iteration": iteration, "failure_category": failure_analysis.get("category")},
    ):
        revised_patch: Patch = await model_provider.coder.generate_structured(
            messages, Patch
        )
        _validator.validate(revised_patch)

    revised_dict = revised_patch.model_dump()
    patch_history.append(revised_dict)

    logger.info(
        "patch_revision_complete",
        run_id=run_id,
        files_revised=len(revised_patch.files),
        summary=revised_patch.summary[:120],
    )

    return {
        "current_patch": revised_dict,
        "patch_history": patch_history,
    }
