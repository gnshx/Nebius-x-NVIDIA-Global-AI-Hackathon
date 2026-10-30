"""
RepoMedic — Joint Validation Rate (JVR) Auditor (SWEPatchTest 2026)

Implements the Joint Validation Rate (JVR) metric from SWEPatchTest (arXiv Oct 2026):
"Evaluating Software Tests Beyond Reproduction".

Evaluates synthesized test oracles across three essential dimensions:
1. Reproduction Fidelity (R_fid): Does the test assert the exact failure mode or expected exception?
2. Positive Conformance (P_conf): Does the test pass against the validated fix?
3. Negative Discrimination (N_disc): Does the test reject empty or cheat patches without tautologies?

A test suite with high JVR confirms that tests do not simply pass superficially,
but actively discriminate correct vs defective implementations.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class JVRAuditReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    jvr_score: float  # 0.0 to 1.0
    is_jvr_robust: bool
    verdict: str  # "HIGH_FIDELITY" | "ACCEPTABLE" | "SUSPECT_ORACLE"
    reproduction_fidelity: float
    positive_conformance: float
    negative_discrimination: float
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "jvr_score": self.jvr_score,
            "is_jvr_robust": self.is_jvr_robust,
            "verdict": self.verdict,
            "reproduction_fidelity": self.reproduction_fidelity,
            "positive_conformance": self.positive_conformance,
            "negative_discrimination": self.negative_discrimination,
            "details": self.details,
        }


class JointValidationAuditor:
    """Audits generated test suites against SWEPatchTest Joint Validation Rate criteria."""

    TAUTOLOGY_PATTERN = re.compile(r"^\+\s*assert\s+(?:True|1\s*==\s*1|True\s*==\s*True)\b", re.MULTILINE)
    SKIP_PATTERN = re.compile(r"^\+\s*@pytest\.mark\.skip\b", re.MULTILINE)
    EXCEPTION_ASSERTION_PATTERN = re.compile(r"pytest\.raises\s*\(\s*(?:ValueError|TypeError|KeyError|IndexError|AttributeError|Exception)\b")
    VALID_ASSERT_PATTERN = re.compile(r"^\+\s*assert\s+.+", re.MULTILINE)

    @classmethod
    def evaluate_jvr(
        cls,
        test_diff: str,
        expected_failure_type: str = "",
        test_passed: bool = True,
        has_tautologies: bool = False,
    ) -> JVRAuditReport:
        """Calculates Joint Validation Rate (JVR) across reproduction, conformance, and discrimination."""
        if not test_diff or not test_diff.strip():
            return JVRAuditReport(
                jvr_score=0.0,
                is_jvr_robust=False,
                verdict="SUSPECT_ORACLE",
                reproduction_fidelity=0.0,
                positive_conformance=0.0,
                negative_discrimination=0.0,
                details="Empty test diff provided; cannot compute Joint Validation Rate.",
            )

        # 1. Reproduction Fidelity (R_fid)
        # Checks if test includes explicit pytest.raises or asserts expected exception/condition
        has_exception_raise = bool(cls.EXCEPTION_ASSERTION_PATTERN.search(test_diff))
        assert_count = len(cls.VALID_ASSERT_PATTERN.findall(test_diff))
        if has_exception_raise:
            assert_count += 1

        r_fid = 0.5
        if has_exception_raise:
            r_fid = 1.0
        elif expected_failure_type and expected_failure_type.lower() in test_diff.lower():
            r_fid = 0.9
        elif assert_count >= 2:
            r_fid = 0.8
        elif assert_count == 1:
            r_fid = 0.6

        # 2. Positive Conformance (P_conf)
        p_conf = 1.0 if test_passed else 0.0

        # 3. Negative Discrimination (N_disc)
        has_local_tautology = bool(cls.TAUTOLOGY_PATTERN.search(test_diff)) or has_tautologies
        has_skip = bool(cls.SKIP_PATTERN.search(test_diff))

        n_disc = 1.0
        if has_skip:
            n_disc = 0.0
        elif has_local_tautology:
            n_disc = 0.2
        elif assert_count == 0:
            n_disc = 0.1

        # Composite JVR calculation: weighted average
        jvr = round((r_fid * 0.35 + p_conf * 0.35 + n_disc * 0.30), 2)
        is_robust = jvr >= 0.75 and n_disc >= 0.7 and p_conf == 1.0

        if jvr >= 0.85 and is_robust:
            verdict = "HIGH_FIDELITY"
        elif is_robust:
            verdict = "ACCEPTABLE"
        else:
            verdict = "SUSPECT_ORACLE"

        details = (
            f"JVR {jvr*100:.0f}% ({verdict}): "
            f"Reproduction Fidelity={r_fid*100:.0f}%, "
            f"Positive Conformance={p_conf*100:.0f}%, "
            f"Negative Discrimination={n_disc*100:.0f}%."
        )

        logger.info(
            "jvr_audit_complete",
            jvr_score=jvr,
            is_robust=is_robust,
            verdict=verdict,
            r_fid=r_fid,
            p_conf=p_conf,
            n_disc=n_disc,
        )

        return JVRAuditReport(
            jvr_score=jvr,
            is_jvr_robust=is_robust,
            verdict=verdict,
            reproduction_fidelity=r_fid,
            positive_conformance=p_conf,
            negative_discrimination=n_disc,
            details=details,
        )
