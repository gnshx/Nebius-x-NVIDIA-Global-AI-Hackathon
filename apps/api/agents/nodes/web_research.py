"""
RepoMedic — Node: WEB_RESEARCH

Performs a targeted web search via Tavily to gather information required to
fix a dependency or environment error that the LLM cannot solve from context
alone.

Only invoked when `failure_analysis.requires_research=True`.
Prefers official documentation domains (docs.*, pypi.org, github.com).
Appends a ResearchResult to `research_results` and persists a ResearchQuery
to the database.
"""

from __future__ import annotations

import uuid

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from db.database import AsyncSessionLocal
from models.orm import ResearchQuery
from models.enums import StepType
from services.tavily.client import tavily_client

logger = structlog.get_logger(__name__)

# Preferred documentation domains for official library info
_PREFERRED_DOMAINS = [
    "docs.python.org",
    "pypi.org",
    "github.com",
    "stackoverflow.com",
    "readthedocs.io",
    "packaging.python.org",
]


async def run(state: RepoMedicState) -> dict:
    """Run a Tavily web search and persist the result."""
    failure_analysis = state.get("failure_analysis") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    research_results: list[dict] = list(state.get("research_results") or [])

    query: str = failure_analysis.get("research_query") or failure_analysis.get("root_cause", "")
    reason: str = failure_analysis.get("root_cause", "unknown failure")

    if not query:
        logger.warning("web_research_no_query", run_id=run_id)
        return {"research_results": research_results}

    logger.info("web_research_start", run_id=run_id, query=query, iteration=iteration)

    async with node_context(
        run_id,
        StepType.WEB_RESEARCH,
        iteration,
        None,
        {"query": query[:200], "iteration": iteration},
    ):
        result = await tavily_client.search(
            query=query,
            reason=reason,
            max_results=5,
            include_domains=_PREFERRED_DOMAINS,
        )

        # Persist ResearchQuery to DB for audit/display
        async with AsyncSessionLocal() as session:
            rq = ResearchQuery(
                id=uuid.uuid4(),
                agent_run_id=uuid.UUID(run_id),
                query=query,
                reason=reason,
                results=[r.model_dump() for r in result.results],
                selected_sources=result.selected_sources,
            )
            session.add(rq)
            await session.commit()

    result_dict = result.model_dump()
    research_results.append(result_dict)

    logger.info(
        "web_research_complete",
        run_id=run_id,
        sources=result.selected_sources,
        num_results=len(result.results),
    )

    return {"research_results": research_results}
