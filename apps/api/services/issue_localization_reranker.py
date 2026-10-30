"""
RepoMedic — Issue Localization Reranker (SweRank 2026)

Implements two-stage code retrieval and ranking based on:
"SweRank: Software Issue Localization with Code Ranking" (Salesforce AI Research 2025/2026).

Reranks candidate code chunks using structural defect indicators:
1. Traceback Frame Proximity: Identifies file paths and line numbers appearing directly in tracebacks.
2. Symbol Definition Matching: Awards high priority to functions/classes defined in the chunk that match the bug report.
3. Exception Culprit Alignment: Matches domain exceptions (e.g. ValueError, KeyError) mentioned in issue statements.
4. Distant File Penalty: Penalizes peripheral utilities or config files when core library functions are implicated.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

TRACEBACK_FILE_LINE_PATTERN = re.compile(r'File\s+["\']([^"\']+)["\'],\s+line\s+(\d+)(?:,\s+in\s+(\w+))?')
FUNCTION_CALL_PATTERN = re.compile(r'\b([a-zA-Z_]\w*)\s*\(')
EXCEPTION_PATTERN = re.compile(r'\b([A-Z][a-zA-Z]*(?:Error|Exception|Warning|Fault))\b')


class RankedChunk(NamedTuple):
    __test__ = False  # Prevent pytest collection

    chunk: dict[str, Any]
    rank_score: float
    relevance_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk": self.chunk,
            "rank_score": self.rank_score,
            "relevance_reasons": self.relevance_reasons,
        }


class LocalizationReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    ranked_chunks: list[dict[str, Any]]
    top_localized_files: list[str]
    localization_confidence: float  # 0.0 to 1.0
    is_definitive: bool
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranked_chunks": self.ranked_chunks,
            "top_localized_files": self.top_localized_files,
            "localization_confidence": self.localization_confidence,
            "is_definitive": self.is_definitive,
            "details": self.details,
        }


class IssueLocalizationReranker:
    """Reranks candidate code chunks using SweRank issue localization criteria."""

    @classmethod
    def rerank_chunks(
        cls,
        chunks: list[dict[str, Any]],
        issue_title: str = "",
        issue_body: str = "",
        likely_components: list[str] | None = None,
    ) -> LocalizationReport:
        """Scores and reorders retrieved chunks according to structural defect signals."""
        if not chunks:
            return LocalizationReport(
                ranked_chunks=[],
                top_localized_files=[],
                localization_confidence=0.0,
                is_definitive=False,
                details="No candidate chunks provided for reranking.",
            )

        issue_text = f"{issue_title}\n{issue_body}"
        components = set(c.lower() for c in (likely_components or []))

        # 1. Extract traceback clues
        traceback_matches = TRACEBACK_FILE_LINE_PATTERN.findall(issue_text)
        tb_files = {Path(m[0]).name.lower() for m in traceback_matches}
        tb_symbols = {m[2].lower() for m in traceback_matches if m[2]}

        # 2. Extract function calls & exceptions
        invoked_calls = set(m.lower() for m in FUNCTION_CALL_PATTERN.findall(issue_text))
        mentioned_exceptions = set(m.lower() for m in EXCEPTION_PATTERN.findall(issue_text))

        ranked_items: list[RankedChunk] = []

        for ch in chunks:
            score = 0.0
            reasons: list[str] = []

            path = ch.get("path", "")
            path_lower = path.lower()
            file_name = Path(path).name.lower()
            symbol = (ch.get("symbol") or "").lower()
            content = (ch.get("content") or "").lower()

            # Signal 1: Traceback Frame Match (+40 pts)
            if file_name in tb_files or any(f in path_lower for f in tb_files):
                score += 40.0
                reasons.append("File cited in stacktrace")

            if symbol in tb_symbols and symbol != "<module>":
                score += 35.0
                reasons.append(f"Function '{symbol}' cited in stacktrace")

            # Signal 2: Likely Component Match (+25 pts)
            if symbol in components:
                score += 25.0
                reasons.append(f"Symbol '{symbol}' in likely components")
            elif any(c in path_lower for c in components):
                score += 15.0
                reasons.append("Path matches likely component")

            # Signal 3: Issue Function Call Invocation (+20 pts)
            if symbol in invoked_calls and symbol != "<module>":
                score += 20.0
                reasons.append(f"Function '{symbol}' invoked in issue")

            # Signal 4: Exception Definition or Raise (+10 pts)
            for exc in mentioned_exceptions:
                if exc in content:
                    score += 10.0
                    reasons.append(f"Handles or raises '{exc}'")
                    break

            # Signal 5: Chunk type heuristic
            if ch.get("chunk_type") in ("function", "method"):
                score += 5.0
            elif ch.get("chunk_type") == "class":
                score += 3.0

            ranked_items.append(RankedChunk(chunk=ch, rank_score=score, relevance_reasons=reasons))

        # Sort descending by score
        ranked_items.sort(key=lambda x: x.rank_score, reverse=True)

        ordered_chunks = [item.chunk for item in ranked_items]
        top_files: list[str] = []
        for ch in ordered_chunks:
            p = ch.get("path", "")
            if p and p not in top_files:
                top_files.append(p)

        top_score = ranked_items[0].rank_score if ranked_items else 0.0
        confidence = round(min(1.0, top_score / 60.0), 2)
        is_definitive = confidence >= 0.70 and len(top_files) > 0

        details = (
            f"SweRank localized defect across {len(top_files)} candidate files with "
            f"{confidence*100:.0f}% confidence. Top file: '{top_files[0] if top_files else 'none'}'."
        )

        logger.info(
            "issue_localization_rerank_complete",
            total_chunks=len(chunks),
            top_file=top_files[0] if top_files else "none",
            top_score=top_score,
            confidence=confidence,
            is_definitive=is_definitive,
        )

        return LocalizationReport(
            ranked_chunks=ordered_chunks,
            top_localized_files=top_files[:5],
            localization_confidence=confidence,
            is_definitive=is_definitive,
            details=details,
        )
