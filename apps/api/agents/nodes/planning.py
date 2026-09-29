"""
RepoMedic — Node: PLANNING

Uses the planner model to devise a structured implementation plan for fixing
the issue. The plan includes root-cause hypothesis, files to change, tests
to write/update, and risk assessment.

Produces an `ImplementationPlan` stored under `plan` in state.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.orm import StepType
from models.schemas import ImplementationPlan
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)

_MAX_CHUNK_CHARS = 3_000  # per-chunk character cap in context
_TOP_CHUNKS = 10           # maximum chunks passed to the prompt


def _build_context_string(chunks: list[dict], max_chunks: int = _TOP_CHUNKS) -> str:
    """Convert a list of code chunks into a readable context block."""
    parts: list[str] = []
    for chunk in chunks[:max_chunks]:
        path = chunk.get("path", "unknown")
        content = chunk.get("content", "")
        if len(content) > _MAX_CHUNK_CHARS:
            content = content[:_MAX_CHUNK_CHARS] + "\n... [truncated]"
        header = f"### {path}"
        if chunk.get("symbol"):
            header += f" — {chunk['symbol']}"
        parts.append(f"{header}\n```\n{content}\n```")
    return "\n\n".join(parts)


async def run(state: RepoMedicState) -> dict:
    """Generate a structured implementation plan using the planner model."""
    issue = state["issue"]
    issue_analysis = state.get("issue_analysis") or {}
    retrieved_context = state.get("retrieved_context") or []
    repo_structure = state.get("repo_structure") or []
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.planner.model

    context_str = _build_context_string(retrieved_context)
    # Summarise the repo tree (first 100 paths)
    repo_tree_str = "\n".join(repo_structure[:100])

    messages = [
        Message(
            role="user",
            content=(
                "You are a senior engineer creating a precise fix plan for the following bug.\n\n"
                "## Issue\n"
                f"Title: {issue.get('title', '')}\n"
                f"Body: {issue.get('body', '') or '(no body)'}\n\n"
                "## Issue Analysis\n"
                f"Summary: {issue_analysis.get('summary', '')}\n"
                f"Problem: {issue_analysis.get('problem_statement', '')}\n"
                f"Expected: {issue_analysis.get('expected_behavior', '')}\n"
                f"Observed: {issue_analysis.get('observed_behavior', '')}\n"
                f"Components: {', '.join(issue_analysis.get('likely_components', []))}\n"
                f"Acceptance criteria: {'; '.join(issue_analysis.get('acceptance_criteria', []))}\n\n"
                "## Repository Structure (sample)\n"
                f"```\n{repo_tree_str}\n```\n\n"
                "## Relevant Code\n"
                f"{context_str}\n\n"
                "Create a detailed implementation plan. "
                "Be specific about file paths (use paths from the repo structure). "
                "Identify the root cause and every file that must change. "
                "Specify tests to add or modify. Assess risks."
            ),
        )
    ]

    logger.info("planning_start", run_id=run_id, iteration=iteration)

    async with node_context(
        run_id,
        StepType.PLANNING,
        iteration,
        model_used,
        {
            "issue_number": issue.get("number"),
            "context_chunks": len(retrieved_context),
        },
    ):
        plan: ImplementationPlan = await model_provider.planner.generate_structured(
            messages, ImplementationPlan
        )

    logger.info(
        "planning_complete",
        run_id=run_id,
        root_cause=plan.root_cause_hypothesis[:120],
        files_to_modify=plan.files_to_modify,
        test_command=plan.test_command,
    )

    return {"plan": plan.model_dump()}
