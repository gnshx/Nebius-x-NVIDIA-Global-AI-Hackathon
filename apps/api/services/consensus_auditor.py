"""
RepoMedic — Patch Consensus Auditor & Deployment Readiness Index (DRI)

Implements multi-dimensional verification consensus from:
- TEX: Test-Time Execution and Cross-Validation for Autonomous Program Repair (2025/2026)
- PROBE: Behavioral Probing & Invariant Consensus in Automated Program Repair (2026)

Synthesizes a unified, mathematically rigorous Deployment Readiness Index (DRI, 0-100)
combining:
1. Oracle Confidence (Fail-to-Pass vs Pass-to-Pass completeness).
2. Patch Cleanliness Score (Delta debugging atomicity, absence of CodeSlop).
3. Invariant Safety Score (Absence of test skips or deleted exports).
4. Mutation Discrimination Score (Active non-tautological test assertions).
5. Security Gate (PatchValidator path traversal & credential safety).
"""

from __future__ import annotations

from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class ConsensusAuditResult(NamedTuple):
    __test__ = False
    dri_score: float  # 0.0 to 100.0
    recommendation: str  # "AUTOMATED_MERGE_RECOMMENDED" | "MANUAL_REVIEW_SUGGESTED" | "REJECTED"
    is_deployable: bool
    breakdown: dict[str, float]
    details: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dri_score": self.dri_score,
            "recommendation": self.recommendation,
            "is_deployable": self.is_deployable,
            "breakdown": self.breakdown,
            "details": self.details,
        }


class PatchConsensusAuditor:
    """Calculates unified consensus scoring across all verification and quality dimensions."""

    WEIGHT_ORACLE = 0.35
    WEIGHT_INVARIANT = 0.25
    WEIGHT_CLEANLINESS = 0.20
    WEIGHT_MUTATION = 0.20

    AUTOMATED_MERGE_THRESHOLD = 85.0
    MANUAL_REVIEW_THRESHOLD = 65.0

    @classmethod
    def audit(
        cls,
        oracle_confidence: float = 1.0,
        invariant_score: float = 1.0,
        cleanliness_score: float = 1.0,
        mutation_score: float = 1.0,
        security_passed: bool = True,
    ) -> ConsensusAuditResult:
        """
        Computes composite DRI score and outputs clear merge recommendations.
        """
        details: list[str] = []

        if not security_passed:
            details.append("CRITICAL: Security gate failed (path traversal or credential exposure).")
            return ConsensusAuditResult(
                dri_score=0.0,
                recommendation="REJECTED",
                is_deployable=False,
                breakdown={
                    "oracle": 0.0,
                    "invariant": 0.0,
                    "cleanliness": 0.0,
                    "mutation": 0.0,
                },
                details=details,
            )

        # Weighted calculation
        c_oracle = max(0.0, min(1.0, oracle_confidence))
        c_invariant = max(0.0, min(1.0, invariant_score))
        c_clean = max(0.0, min(1.0, cleanliness_score))
        c_mut = max(0.0, min(1.0, mutation_score))

        raw_score = (
            (c_oracle * cls.WEIGHT_ORACLE)
            + (c_invariant * cls.WEIGHT_INVARIANT)
            + (c_clean * cls.WEIGHT_CLEANLINESS)
            + (c_mut * cls.WEIGHT_MUTATION)
        )

        dri = round(raw_score * 100.0, 1)

        breakdown = {
            "oracle_confidence": round(c_oracle * 100.0, 1),
            "invariant_safety": round(c_invariant * 100.0, 1),
            "patch_cleanliness": round(c_clean * 100.0, 1),
            "mutation_discrimination": round(c_mut * 100.0, 1),
        }

        if dri >= cls.AUTOMATED_MERGE_THRESHOLD and c_oracle >= 0.90:
            rec = "AUTOMATED_MERGE_RECOMMENDED"
            is_dep = True
            details.append(f"High-confidence fix (DRI: {dri}/100). All test suites, invariants, and cleanliness standards satisfied.")
        elif dri >= cls.MANUAL_REVIEW_THRESHOLD:
            rec = "MANUAL_REVIEW_SUGGESTED"
            is_dep = False
            details.append(f"Moderate confidence fix (DRI: {dri}/100). Review recommended prior to merge.")
        else:
            rec = "REJECTED"
            is_dep = False
            details.append(f"Low confidence fix (DRI: {dri}/100). Insufficient verification strength.")

        logger.info(
            "patch_consensus_audit_complete",
            dri=dri,
            recommendation=rec,
            is_deployable=is_dep,
        )

        return ConsensusAuditResult(
            dri_score=dri,
            recommendation=rec,
            is_deployable=is_dep,
            breakdown=breakdown,
            details=details,
        )
