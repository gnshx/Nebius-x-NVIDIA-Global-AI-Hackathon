"""
RepoMedic — Node: TEST_GENERATION

Uses the coder model to generate regression tests that prove the bug fix works.
Tests are generated as unified diffs for new or modified test files, then merged
into `current_patch.files`.

Prefers modifying existing test files over creating new ones when the plan
specifies `tests_to_modify`.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.orm import StepType
from models.schemas import FileChange, Patch
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_MAX_CHUNK_CHARS = 2_000


def _format_patch_summary(patch: dict) -> str:
    """Render the current implementation patch as a readable summary."""
    files = patch.get("files", [])
    lines = [f"Summary: {patch.get('summary', '')}"]
    for f in files:
        lines.append(f"  [{f.get('operation', '?')}] {f.get('path', '?')} — {f.get('reason', '')}")
    return "\n".join(lines)


async def run(state: RepoMedicState) -> dict:
    """Generate regression tests and merge them into the current patch."""
    plan = state.get("plan") or {}
    issue_analysis = state.get("issue_analysis") or {}
    issue = state.get("issue") or {}
    retrieved_context = state.get("retrieved_context") or []
    current_patch = state.get("current_patch") or {"files": [], "summary": "", "test_command": "pytest"}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.coder.model

    tests_to_add: list[str] = plan.get("tests_to_add", [])
    tests_to_modify: list[str] = plan.get("tests_to_modify", [])

    # Build context from existing test chunks
    test_chunks = [
        c for c in retrieved_context
        if "test" in c.get("path", "").lower() or c.get("chunk_type") == "test"
    ][:6]
    test_ctx = "\n\n".join(
        f"### {c.get('path', '')}\n```\n{c.get('content', '')[:_MAX_CHUNK_CHARS]}\n```"
        for c in test_chunks
    )

    patch_summary = _format_patch_summary(current_patch)

    messages = [
        Message(
            role="system",
            content=(
                "You are an expert test engineer. Generate regression tests that verify "
                "the bug fix. Return a Patch with only test file changes. "
                "Use proper unified diff format. Prefer modifying existing files."
            ),
        ),
        Message(
            role="user",
            content=(
                "## Issue\n"
                f"Title: {issue.get('title', '')}\n"
                f"Problem: {issue_analysis.get('problem_statement', '')}\n"
                f"Expected behavior: {issue_analysis.get('expected_behavior', '')}\n"
                f"Acceptance criteria: {'; '.join(issue_analysis.get('acceptance_criteria', []))}\n\n"
                "## Applied Implementation Patch\n"
                f"{patch_summary}\n\n"
                "## Tests to Add\n"
                + ("\n".join(f"  - {t}" for t in tests_to_add) or "  (none specified — infer from issue)") + "\n\n"
                "## Tests to Modify\n"
                + ("\n".join(f"  - {t}" for t in tests_to_modify) or "  (none)") + "\n\n"
                "## Existing Test Code\n"
                f"{test_ctx or '(no existing tests retrieved)'}\n\n"
                "Generate minimal, focused regression tests. Each test must directly "
                "verify the fixed behavior. Include at least one test that would have "
                "FAILED before the fix and PASSES after."
            ),
        ),
    ]

    logger.info(
        "test_generation_start",
        run_id=run_id,
        tests_to_add=tests_to_add,
        tests_to_modify=tests_to_modify,
    )

    async with node_context(
        run_id,
        StepType.TEST_GENERATION,
        iteration,
        model_used,
        {"tests_to_add": tests_to_add, "tests_to_modify": tests_to_modify},
    ):
        test_patch: Patch = await model_provider.coder.generate_structured(messages, Patch)

    # Merge test file changes into current_patch (deduplicate by path)
    existing_files: dict[str, dict] = {f["path"]: f for f in current_patch.get("files", [])}
    for test_change in test_patch.files:
        existing_files[test_change.path] = test_change.model_dump()

    merged_patch = {
        **current_patch,
        "files": list(existing_files.values()),
    }

    logger.info(
        "test_generation_complete",
        run_id=run_id,
        test_files_generated=len(test_patch.files),
        total_files_in_patch=len(merged_patch["files"]),
    )

    return {
        "current_patch": merged_patch,
        "generated_tests": [fc.model_dump() for fc in test_patch.files],
    }
