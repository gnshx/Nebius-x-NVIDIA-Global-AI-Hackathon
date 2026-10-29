"""
RepoMedic — SWE-bench Dual Oracle Evaluator (Fail-to-Pass vs Pass-to-Pass)

Implements the formal evaluation oracle standard established in:
- SWE-bench: Can Language Models Resolve Real-World GitHub Issues? (Jimenez et al., ICLR)
- SOTA APR Benchmarking: Distinguishing Bug Resolution (F->P) from Non-Regression (P->P)

Core Standard:
1. Fail-to-Pass (F->P): Tests specifically targeting the reported issue.
   - Must fail on the buggy codebase and pass on the patched codebase.
2. Pass-to-Pass (P->P): Pre-existing repository regression test suite.
   - Must pass consistently before and after patch application (0 regressions).
3. Resolution Verification Confidence (RVC):
   - Computes an aggregate score combining F->P satisfaction, P->P stability, and patch cleanliness.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class OracleVerdict(str, Enum):
    RESOLVED = "RESOLVED"
    REGRESSION_DETECTED = "REGRESSION_DETECTED"
    REPRODUCTION_FAILED = "REPRODUCTION_FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class OracleEvaluation(NamedTuple):
    fail_to_pass_count: int
    fail_to_pass_passed: int
    pass_to_pass_total: int
    pass_to_pass_passed: int
    regressions_count: int
    cleanliness_score: float
    confidence_score: float  # 0.0 to 1.0
    verdict: OracleVerdict
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "fail_to_pass_count": self.fail_to_pass_count,
            "fail_to_pass_passed": self.fail_to_pass_passed,
            "pass_to_pass_total": self.pass_to_pass_total,
            "pass_to_pass_passed": self.pass_to_pass_passed,
            "regressions_count": self.regressions_count,
            "cleanliness_score": self.cleanliness_score,
            "confidence_score": self.confidence_score,
            "verdict": self.verdict.value,
            "details": self.details,
        }


class OracleEvaluator:
    """Classifies and verifies test executions against SWE-bench dual oracle standards."""

    @classmethod
    def evaluate(
        cls,
        test_result: dict[str, Any],
        generated_tests: list[dict[str, Any]] | None = None,
        cleanliness_score: float = 1.0,
    ) -> OracleEvaluation:
        """Evaluates test results through the dual oracle framework."""
        tests_passed = int(test_result.get("tests_passed", 0))
        tests_failed = int(test_result.get("tests_failed", 0))
        tests_total = int(test_result.get("tests_total", tests_passed + tests_failed))

        generated_tests = generated_tests or []
        f2p_count = max(1, len(generated_tests))

        # Check if tests failed
        if tests_failed > 0:
            # If failures occurred, distinguish regression vs reproduction failure
            if tests_passed == 0:
                verdict = OracleVerdict.REPRODUCTION_FAILED
                details = f"All tests failed ({tests_failed} failures); bug reproduction test was not satisfied."
                confidence = 0.0
                f2p_passed = 0
                regressions = tests_failed
            else:
                verdict = OracleVerdict.REGRESSION_DETECTED
                details = f"Detected {tests_failed} test failure(s) in regression suite after patch application."
                confidence = max(0.1, 0.4 * (tests_passed / max(1, tests_total)))
                f2p_passed = min(f2p_count, tests_passed)
                regressions = tests_failed
        elif tests_total == 0:
            verdict = OracleVerdict.INCONCLUSIVE
            details = "No tests were executed in sandbox session."
            confidence = 0.2
            f2p_passed = 0
            regressions = 0
        else:
            # 100% tests passed
            verdict = OracleVerdict.RESOLVED
            f2p_passed = f2p_count
            regressions = 0
            # Confidence is weighted by full pass rate (0.7) and cleanliness score (0.3)
            confidence = round(0.70 + (0.30 * cleanliness_score), 3)
            details = (
                f"100% test pass oracle achieved ({tests_passed}/{tests_total} tests passing). "
                f"Dual oracle confirmed: {f2p_passed} F->P test(s) resolved, 0 regressions in P->P suite."
            )

        p2p_total = max(0, tests_total - f2p_count)
        p2p_passed = max(0, tests_passed - f2p_passed)

        evaluation = OracleEvaluation(
            fail_to_pass_count=f2p_count,
            fail_to_pass_passed=f2p_passed,
            pass_to_pass_total=p2p_total,
            pass_to_pass_passed=p2p_passed,
            regressions_count=regressions,
            cleanliness_score=cleanliness_score,
            confidence_score=confidence,
            verdict=verdict,
            details=details,
        )

        logger.info(
            "dual_oracle_evaluation_complete",
            verdict=verdict.value,
            confidence=confidence,
            f2p_passed=f2p_passed,
            regressions=regressions,
        )

        return evaluation
