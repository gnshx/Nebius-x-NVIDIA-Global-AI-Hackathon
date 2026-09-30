"""
RepoMedic — Node: IMPLEMENTATION

Uses the coder model to generate a unified-diff patch that fixes the issue
according to the plan. The patch is validated for security before being
stored in state.

Appends the validated patch to `patch_history` and sets `current_patch`.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.enums import StepType
from models.schemas import Patch
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_MAX_CHUNK_CHARS = 2_500
_TOP_CHUNKS = 8


class PatchValidator:
    """Security-oriented validator for generated patches."""

    BLOCKED_PATH_PATTERNS = [".git/", "..", "/etc/", "/proc/"]
    BLOCKED_EXTENSIONS = [".pem", ".key", ".env", ".p12"]

    def validate(self, patch: Patch) -> None:
        """Raise ValueError if any FileChange violates security rules."""
        for change in patch.files:
            for pattern in self.BLOCKED_PATH_PATTERNS:
                if pattern in change.path:
                    raise ValueError(f"Blocked path pattern in: {change.path}")
            if change.path.startswith("/"):
                raise ValueError(f"Absolute path rejected: {change.path}")
            for ext in self.BLOCKED_EXTENSIONS:
                if change.path.endswith(ext):
                    raise ValueError(f"Blocked file extension: {change.path}")


_validator = PatchValidator()


def _chunk_context(chunks: list[dict], top_n: int = _TOP_CHUNKS) -> str:
    parts: list[str] = []
    for chunk in chunks[:top_n]:
        path = chunk.get("path", "unknown")
        content = chunk.get("content", "")
        if len(content) > _MAX_CHUNK_CHARS:
            content = content[:_MAX_CHUNK_CHARS] + "\n... [truncated]"
        parts.append(f"### {path}\n```\n{content}\n```")
    return "\n\n".join(parts)


async def run(state: RepoMedicState) -> dict:
    """Generate a validated code patch using the coder model."""
    plan = state.get("plan") or {}
    retrieved_context = state.get("retrieved_context") or []
    issue_analysis = state.get("issue_analysis") or {}
    issue = state.get("issue") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    patch_history: list[dict] = list(state.get("patch_history") or [])
    model_used = model_provider.coder.model

    context_str = _chunk_context(retrieved_context)
    files_to_modify = "\n".join(f"  - {f}" for f in plan.get("files_to_modify", []))
    files_to_add = "\n".join(f"  - {f}" for f in plan.get("files_to_add", []))

    messages = [
        Message(
            role="system",
            content=(
                "You are an expert software engineer. Generate unified diff patches "
                "that fix exactly the described bug. Each patch in the `files` list must "
                "have: path (relative), operation (modify|create|delete), patch (valid "
                "unified diff starting with --- and +++), and reason."
            ),
        ),
        Message(
            role="user",
            content=(
                "## Bug Report\n"
                f"Title: {issue.get('title', '')}\n"
                f"Summary: {issue_analysis.get('summary', '')}\n"
                f"Problem: {issue_analysis.get('problem_statement', '')}\n"
                f"Expected: {issue_analysis.get('expected_behavior', '')}\n"
                f"Observed: {issue_analysis.get('observed_behavior', '')}\n\n"
                "## Plan\n"
                f"Root cause: {plan.get('root_cause_hypothesis', '')}\n"
                f"Changes required:\n{chr(10).join(plan.get('changes', []))}\n\n"
                "## Files to Modify\n"
                f"{files_to_modify or '(none)'}\n\n"
                "## Files to Create\n"
                f"{files_to_add or '(none)'}\n\n"
                "## Relevant Code\n"
                f"{context_str}\n\n"
                "Generate a minimal, correct unified diff patch for each affected file. "
                "Use proper --- a/path +++ b/path @@ hunk format. "
                "Do NOT include test files — those come later."
            ),
        ),
    ]

    logger.info(
        "implementation_start",
        run_id=run_id,
        iteration=iteration,
        files_to_modify=plan.get("files_to_modify"),
    )

    async with node_context(
        run_id,
        StepType.IMPLEMENTATION,
        iteration,
        model_used,
        {"files_to_modify": plan.get("files_to_modify"), "iteration": iteration},
    ):
        patch: Patch = await model_provider.coder.generate_structured(messages, Patch)
        _validator.validate(patch)

    patch_dict = patch.model_dump()
    patch_history.append(patch_dict)

    logger.info(
        "implementation_complete",
        run_id=run_id,
        files_changed=len(patch.files),
        summary=patch.summary[:120],
    )

    return {
        "current_patch": patch_dict,
        "patch_history": patch_history,
    }
