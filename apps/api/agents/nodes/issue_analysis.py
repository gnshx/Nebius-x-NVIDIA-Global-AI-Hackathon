"""
RepoMedic — Node: ISSUE_ANALYSIS

Uses the planner model (NVIDIA Nemotron) to extract structured information
from a GitHub issue. Self-heals by fetching the issue if not already present
in the state.
"""

from __future__ import annotations

from pathlib import Path
import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from models.enums import StepType
from models.schemas import IssueAnalysis
from services.github.client import github_client
from services.nebius.client import Message, model_provider

logger = structlog.get_logger(__name__)


async def _resolve_issue_and_repo(state: RepoMedicState) -> tuple[dict, dict]:
    """Ensure issue and repository dicts are present, resolving via GitHub or local fallback."""
    issue = state.get("issue")
    repository = state.get("repository")
    full_name = state.get("repository_full_name", "")
    issue_number = state.get("issue_number", 1)
    installation_id = state.get("installation_id", 0)

    if not repository:
        repository = {
            "full_name": full_name,
            "name": full_name.split("/")[-1] if "/" in full_name else full_name,
            "language": "Python",
        }

    if not issue:
        # Try fetching via GitHub App client
        if installation_id and full_name:
            try:
                issue = await github_client.get_issue(installation_id, full_name, issue_number)
            except Exception as e:
                logger.warning("issue_fetch_failed_using_fallback", error=str(e))

        # Local fallback (for demo repository or offline testing)
        if not issue:
            demo_issue_file = Path("demo/ISSUE.md")
            if demo_issue_file.exists():
                text = demo_issue_file.read_text(encoding="utf-8")
                issue = {
                    "number": issue_number,
                    "title": "parse_user_id crashes with IndexError: list index out of range",
                    "body": text,
                    "state": "open",
                }
            else:
                issue = {
                    "number": issue_number,
                    "title": f"Bug reported in issue #{issue_number}",
                    "body": "Investigate and resolve the failing behavior in the repository.",
                    "state": "open",
                }

    return issue, repository


async def run(state: RepoMedicState) -> dict:
    """Analyze a GitHub issue and extract structured metadata."""
    issue, repository = await _resolve_issue_and_repo(state)
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
            role="system",
            content=(
                "You are an elite staff AI engineer analyzing software bug reports. "
                "Extract root cause indicators, expected vs observed behaviors, "
                "and precise acceptance criteria."
            ),
        ),
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
        ),
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

    return {
        "issue": issue,
        "repository": repository,
        "issue_analysis": analysis.model_dump(),
    }
