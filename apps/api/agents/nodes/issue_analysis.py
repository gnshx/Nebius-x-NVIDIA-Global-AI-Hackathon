"""
RepoMedic — Node: ISSUE_ANALYSIS

Uses the planner model to extract structured information from a GitHub issue.
Populates the `issue_analysis` key in state with an IssueAnalysis schema instance.
"""

from __future__ import annotations

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.orm import StepType
from models.schemas import IssueAnalysis
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)


async def run(state: RepoMedicState) -> dict:
    """Analyze a GitHub issue and extract structured metadata."""
    issue = state["issue"]
    repository = state["repository"]
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    model_used = model_provider.planner.model

    logger.info(
        "issue_analysis_start",
        run_id=run_id,
        issue_number=issue.get("number"),
        repo=repository.get("full_name"),
    )

    messages = [
        Message(
            role="user",
            content=(
                "Analyze this GitHub issue and extract structured information about the bug:\n\n"
                f"- Issue title: {issue.get('title', '')}\n"
                f"- Issue body: {issue.get('body', '') or '(no body)'}\n"
                f"- Repository: {repository.get('full_name', '')}\n"
                f"- Languages: {repository.get('language', 'unknown')}\n\n"
                "Identify the problem statement, expected vs observed behavior, "
                "likely source components, relevant files, and acceptance criteria."
            ),
        )
    ]

    async with node_context(
        run_id,
        StepType.ISSUE_ANALYSIS,
        iteration,
        model_used,
        {"issue_number": issue.get("number"), "repo": repository.get("full_name")},
    ):
        analysis: IssueAnalysis = await model_provider.planner.generate_structured(
            messages, IssueAnalysis
        )

    logger.info(
        "issue_analysis_complete",
        run_id=run_id,
        summary=analysis.summary[:120],
        components=analysis.likely_components,
        confidence=analysis.confidence,
    )

    return {"issue_analysis": analysis.model_dump()}
