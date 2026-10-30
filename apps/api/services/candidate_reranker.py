"""
RepoMedic — Test-Time Multi-Candidate Patch Reranker

Implements test-time compute scaling and patch selection from:
- Agentless: Demystifying LLM-based Software Engineering (ICSE 2025)
- SWE-Reasoner & Maestro: Test-Time Compute Optimization in APR (2025/2026)

Evaluates and ranks candidate patches using multi-dimensional quality metrics:
1. Edit Parsimony: Rewards atomic, localized diffs; penalizes extraneous file touches.
2. Invariant Safety: Verifies preservation of public API exports and test cases.
3. Cleanliness: Rewards normalized line-endings and absence of CodeSlop.
"""

from __future__ import annotations

from typing import Any, NamedTuple
import structlog

from services.cross_validator import PatchCrossValidator
from services.patch_minimizer import PatchMinimizer
from models.schemas import Patch

logger = structlog.get_logger(__name__)


class RankedCandidate(NamedTuple):
    __test__ = False
    patch: dict[str, Any]
    rank: int
    composite_score: float  # 0.0 to 100.0
    parsimony_score: float  # 0.0 to 1.0
    invariant_score: float  # 0.0 to 1.0
    cleanliness_score: float  # 0.0 to 1.0
    selection_reason: str


class RerankingResult(NamedTuple):
    __test__ = False
    champion_patch: dict[str, Any]
    total_candidates_evaluated: int
    candidates: list[RankedCandidate]

    def to_dict(self) -> dict[str, Any]:
        return {
            "champion_patch": self.champion_patch,
            "total_candidates_evaluated": self.total_candidates_evaluated,
            "candidates": [
                {
                    "rank": c.rank,
                    "composite_score": c.composite_score,
                    "parsimony_score": c.parsimony_score,
                    "invariant_score": c.invariant_score,
                    "cleanliness_score": c.cleanliness_score,
                    "selection_reason": c.selection_reason,
                    "summary": c.patch.get("summary", ""),
                }
                for c in self.candidates
            ],
        }


class MultiCandidateReranker:
    """Evaluates a pool of candidate patches and selects the optimal champion."""

    WEIGHT_PARSIMONY = 0.30
    WEIGHT_INVARIANT = 0.40
    WEIGHT_CLEANLINESS = 0.30

    @classmethod
    def calculate_parsimony(cls, patch: dict[str, Any]) -> float:
        """Scores diff atomicity (fewer touched files and lines yields higher score)."""
        files = patch.get("files", [])
        if not files:
            return 0.5

        # Penalize excessive file touches for a single bug fix
        file_penalty = max(0.0, 1.0 - (0.2 * max(0, len(files) - 1)))

        total_lines_changed = 0
        for f in files:
            diff = f.get("diff", "") or f.get("patch", "") or ""
            additions = len([l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")])
            deletions = len([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")])
            total_lines_changed += additions + deletions

        # Ideal bug fix is 1-25 lines; penalize massive rewrites
        if total_lines_changed <= 25:
            line_score = 1.0
        elif total_lines_changed <= 60:
            line_score = 0.80
        elif total_lines_changed <= 150:
            line_score = 0.50
        else:
            line_score = 0.20

        return round(0.5 * file_penalty + 0.5 * line_score, 2)

    @classmethod
    def rerank(cls, candidates: list[dict[str, Any]]) -> RerankingResult:
        """Reranks candidate patches and identifies the champion."""
        if not candidates:
            empty_patch = {"summary": "Empty", "files": []}
            return RerankingResult(
                champion_patch=empty_patch,
                total_candidates_evaluated=0,
                candidates=[],
            )

        scored: list[RankedCandidate] = []

        for patch in candidates:
            files = patch.get("files", [])

            # 1. Parsimony score
            parsimony = cls.calculate_parsimony(patch)

            # 2. Invariant safety score
            cross_report = PatchCrossValidator.validate_patch(files)
            inv_score = cross_report.invariant_score if cross_report.is_safe else 0.1

            # 3. Cleanliness score
            try:
                patch_obj = Patch(**patch) if files else Patch(summary="Review", files=[])
                clean_metrics = PatchMinimizer.evaluate_metrics(patch_obj)
                clean_score = clean_metrics.cleanliness_score
            except Exception:
                clean_score = 0.90

            composite = (
                (parsimony * cls.WEIGHT_PARSIMONY)
                + (inv_score * cls.WEIGHT_INVARIANT)
                + (clean_score * cls.WEIGHT_CLEANLINESS)
            ) * 100.0

            reasons: list[str] = []
            if parsimony >= 0.80:
                reasons.append("atomic edit distance")
            if inv_score == 1.0:
                reasons.append("zero invariant violations")
            if clean_score >= 0.90:
                reasons.append("zero codeslop")

            scored.append(
                RankedCandidate(
                    patch=patch,
                    rank=0,
                    composite_score=round(composite, 1),
                    parsimony_score=parsimony,
                    invariant_score=inv_score,
                    cleanliness_score=clean_score,
                    selection_reason=", ".join(reasons) or "baseline patch",
                )
            )

        # Sort descending by composite score
        scored.sort(key=lambda x: x.composite_score, reverse=True)

        ranked: list[RankedCandidate] = []
        for i, cand in enumerate(scored):
            ranked.append(
                RankedCandidate(
                    patch=cand.patch,
                    rank=i + 1,
                    composite_score=cand.composite_score,
                    parsimony_score=cand.parsimony_score,
                    invariant_score=cand.invariant_score,
                    cleanliness_score=cand.cleanliness_score,
                    selection_reason=cand.selection_reason,
                )
            )

        champion = ranked[0].patch

        logger.info(
            "multi_candidate_reranking_complete",
            total_evaluated=len(candidates),
            champion_score=ranked[0].composite_score,
            champion_summary=champion.get("summary", "")[:100],
        )

        return RerankingResult(
            champion_patch=champion,
            total_candidates_evaluated=len(candidates),
            candidates=ranked,
        )
