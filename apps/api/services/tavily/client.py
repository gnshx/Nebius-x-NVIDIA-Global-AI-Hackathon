"""
RepoMedic — Tavily Search Integration

Selectively used for web research during failure analysis.
NOT called for every failure — only for unknown library errors.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel
from tavily import TavilyClient as _TavilyClient

from config import settings

logger = structlog.get_logger(__name__)


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float


class ResearchResult(BaseModel):
    query: str
    reason: str
    results: list[SearchResult]
    selected_sources: list[str]
    timestamp: datetime


class TavilySearchClient:
    def __init__(self) -> None:
        self._client = _TavilyClient(api_key=settings.tavily_api_key.get_secret_value())

    async def search(
        self,
        query: str,
        reason: str,
        max_results: int = 5,
        include_domains: list[str] | None = None,
    ) -> ResearchResult:
        """Perform a web search. Logs the query and reason for auditability."""
        logger.info("tavily_search", query=query, reason=reason)
        kwargs: dict[str, Any] = {"query": query, "max_results": max_results}
        if include_domains:
            kwargs["include_domains"] = include_domains

        raw = self._client.search(**kwargs)
        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
            )
            for r in raw.get("results", [])
        ]
        selected = [r.url for r in results[:3]]

        return ResearchResult(
            query=query,
            reason=reason,
            results=results,
            selected_sources=selected,
            timestamp=datetime.utcnow(),
        )


tavily_client = TavilySearchClient()
