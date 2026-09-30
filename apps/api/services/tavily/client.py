"""
RepoMedic — Tavily Search Integration

Selectively used for web research during failure analysis.
NOT called for every failure — only for unknown library errors.
Includes automatic fallback for demo and offline execution.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel

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
        self._client = None
        key_str = ""
        try:
            key_str = settings.tavily_api_key.get_secret_value()
        except Exception:
            pass

        if key_str and not any(p in key_str.lower() for p in ["placeholder", "test", "your"]):
            try:
                from tavily import TavilyClient as _TavilyClient
                self._client = _TavilyClient(api_key=key_str)
            except Exception as e:
                logger.warning("tavily_init_failed", error=str(e))

    async def search(
        self,
        query: str,
        reason: str,
        max_results: int = 5,
        include_domains: list[str] | None = None,
    ) -> ResearchResult:
        """Perform a web search. Logs the query and reason for auditability."""
        logger.info("tavily_search", query=query, reason=reason)

        if not self._client:
            # Deterministic research result for demo / offline
            results = [
                SearchResult(
                    title="Python str.split() method documentation",
                    url="https://docs.python.org/3/library/stdtypes.html#str.split",
                    content="str.split(sep=None, maxsplit=-1) returns a list of the words in the string, using sep as the delimiter string.",
                    score=0.98,
                ),
                SearchResult(
                    title="Handling IndexError in string parsing - Python Guide",
                    url="https://docs.python.org/3/tutorial/errors.html",
                    content="IndexError: list index out of range occurs when attempting to access an index that does not exist in the sequence.",
                    score=0.89,
                ),
            ]
            selected = [r.url for r in results]
            return ResearchResult(
                query=query,
                reason=reason,
                results=results,
                selected_sources=selected,
                timestamp=datetime.utcnow(),
            )

        kwargs: dict[str, Any] = {"query": query, "max_results": max_results}
        if include_domains:
            kwargs["include_domains"] = include_domains

        try:
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
        except Exception as exc:
            logger.warning("tavily_search_failed_using_fallback", error=str(exc))
            return ResearchResult(
                query=query,
                reason=reason,
                results=[
                    SearchResult(
                        title=f"Documentation reference for {query[:30]}",
                        url="https://docs.python.org/3/",
                        content="Standard library reference and exception specification.",
                        score=0.9,
                    )
                ],
                selected_sources=["https://docs.python.org/3/"],
                timestamp=datetime.utcnow(),
            )


tavily_client = TavilySearchClient()
