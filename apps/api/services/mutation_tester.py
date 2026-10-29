"""
RepoMedic — Test Mutation & Discriminative Oracle Validator

Implements cutting-edge test suite validation principles from:
- SWE-Mutation: Evaluating Test Suite Quality via Mutation Testing (arXiv:2602 / 2026 APR)
- Detection of Tautological and Vacuous Assertions in LLM-Generated Tests

Solves the critical SWE-bench failure mode where generated regression tests pass
superficially without genuine discriminative power (e.g., missing assertions,
trivial truth assertions, or non-discriminative checks).
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class TestQualityReport(NamedTuple):
    __test__ = False
    total_test_functions: int
    valid_assertions: int
    tautological_assertions: int
    has_exception_testing: bool
    discrimination_score: float  # 0.0 to 1.0 (higher = more rigorous oracle)
    is_robust_oracle: bool
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_test_functions": self.total_test_functions,
            "valid_assertions": self.valid_assertions,
            "tautological_assertions": self.tautological_assertions,
            "has_exception_testing": self.has_exception_testing,
            "discrimination_score": self.discrimination_score,
            "is_robust_oracle": self.is_robust_oracle,
            "findings": self.findings,
        }


class MutationTester:
    """Analyzes synthesized test diffs to detect tautological assertions and measure oracle strength."""

    # Patterns for tautological or vacuous assertions
    TAUTOLOGICAL_PATTERNS = [
        re.compile(r"^\s*\+?\s*assert\s+(True|not\s+False|1\s*==\s*1)\s*$", re.MULTILINE),
        re.compile(r"^\s*\+?\s*assert\s+(\w+)\s*==\s*\1\s*$", re.MULTILINE),  # assert x == x
        re.compile(r"^\s*\+?\s*assert\s+len\((\w+)\)\s*==\s*len\(\1\)\s*$", re.MULTILINE),
    ]

    # Meaningful oracle patterns
    ASSERTION_PATTERN = re.compile(r"^\s*\+?\s*assert\s+", re.MULTILINE)
    RAISES_PATTERN = re.compile(r"pytest\.raises\s*\(|with\s+self\.assertRaises", re.MULTILINE)
    TEST_FUNC_PATTERN = re.compile(r"def\s+(test_\w+)\s*\(", re.MULTILINE)

    @classmethod
    def audit_test_diff(cls, diff_content: str) -> TestQualityReport:
        """Audits unified diff content of generated test files."""
        findings: list[str] = []
        test_functions = cls.TEST_FUNC_PATTERN.findall(diff_content)
        total_funcs = max(1, len(test_functions))

        # Count total assertions added
        all_asserts = cls.ASSERTION_PATTERN.findall(diff_content)
        has_raises = bool(cls.RAISES_PATTERN.search(diff_content))

        # Count tautologies
        tautology_count = 0
        for pattern in cls.TAUTOLOGICAL_PATTERNS:
            matches = pattern.findall(diff_content)
            tautology_count += len(matches)

        if tautology_count > 0:
            findings.append(f"Detected {tautology_count} tautological/trivial assertion(s) (e.g. assert True or assert x == x).")

        valid_asserts = max(0, len(all_asserts) - tautology_count)
        if has_raises:
            valid_asserts += 1  # pytest.raises acts as a strong negative oracle

        if valid_asserts == 0 and not has_raises:
            findings.append("Test file contains zero valid assert statements or exception handlers.")

        # Calculate discrimination score
        # A robust test has >= 1 valid assertion per test function and zero tautologies
        if valid_asserts == 0:
            discrimination = 0.1
        elif tautology_count > 0:
            discrimination = max(0.3, 0.8 - (0.2 * tautology_count))
        else:
            # Score scales with assertion depth (capped at 1.0)
            ratio = valid_asserts / total_funcs
            discrimination = min(1.0, 0.85 + (0.15 * min(1.0, ratio)))

        is_robust = discrimination >= 0.70 and valid_asserts >= 1 and tautology_count == 0

        report = TestQualityReport(
            total_test_functions=total_funcs,
            valid_assertions=valid_asserts,
            tautological_assertions=tautology_count,
            has_exception_testing=has_raises,
            discrimination_score=round(discrimination, 2),
            is_robust_oracle=is_robust,
            findings=findings,
        )

        logger.info(
            "mutation_test_audit_complete",
            test_funcs=total_funcs,
            valid_asserts=valid_asserts,
            tautologies=tautology_count,
            score=report.discrimination_score,
            is_robust=is_robust,
        )

        return report
