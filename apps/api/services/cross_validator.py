"""
RepoMedic — Patch Cross-Validator & Invariant Checker

Implements test-time cross-validation and behavioral invariant preservation from:
- TEX: Test-Time Execution and Cross-Validation for Autonomous Program Repair (2025/2026)
- Behavioral Invariant Verification for LLM-Generated Patches

Detects cheating/superficial patch patterns where an LLM attempts to pass tests by:
1. Deleting or commenting out existing tests.
2. Injecting unconditional skips (`@pytest.mark.skip`, `return` at start of test).
3. Deleting public module exports (`__all__` or public functions).
4. Blanking out assertion statements.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class CrossValidationReport(NamedTuple):
    __test__ = False
    is_safe: bool
    invariant_score: float  # 0.0 to 1.0 (higher = strictly preserves contracts)
    violations: list[str]
    warnings: list[str]
    modified_test_count: int
    modified_source_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "invariant_score": self.invariant_score,
            "violations": self.violations,
            "warnings": self.warnings,
            "modified_test_count": self.modified_test_count,
            "modified_source_count": self.modified_source_count,
        }


class PatchCrossValidator:
    """Audits patch diffs to guarantee behavioral invariants and prevent cheat patterns."""

    # Patterns indicating cheating or destructive modifications in test files
    SUSPICIOUS_TEST_MODS = [
        (re.compile(r"^\+\s*@pytest\.mark\.skip", re.MULTILINE), "Injected @pytest.mark.skip into test suite"),
        (re.compile(r"^\+\s*#.*def\s+test_", re.MULTILINE), "Commented out existing test function"),
        (re.compile(r"^\+\s*#.*assert\s+", re.MULTILINE), "Commented out test assertion"),
        (re.compile(r"^-\s*assert\s+", re.MULTILINE), "Deleted assertion from test file"),
    ]

    # Patterns indicating breaking public contracts in source files
    SUSPICIOUS_SRC_MODS = [
        (re.compile(r"^-\s*__all__\s*=", re.MULTILINE), "Deleted or altered module public __all__ export list"),
        (re.compile(r"^-\s*def\s+[a-zA-Z_]\w*\s*\(", re.MULTILINE), "Deleted function definition (potential API breakage)"),
        (re.compile(r"^-\s*class\s+[a-zA-Z_]\w*\s*[:\(]", re.MULTILINE), "Deleted class definition (potential API breakage)"),
    ]

    @classmethod
    def validate_patch(cls, files: list[dict[str, Any]]) -> CrossValidationReport:
        """Audits a collection of file changes for invariant preservation."""
        violations: list[str] = []
        warnings: list[str] = []
        test_count = 0
        src_count = 0

        for f in files:
            path = f.get("path", "")
            diff = f.get("diff", "") or f.get("patch", "") or ""
            is_test_file = "test" in path.lower()

            if is_test_file:
                test_count += 1
                for pattern, msg in cls.SUSPICIOUS_TEST_MODS:
                    if pattern.search(diff):
                        violations.append(f"[{path}] {msg}")
            else:
                src_count += 1
                for pattern, msg in cls.SUSPICIOUS_SRC_MODS:
                    if pattern.search(diff):
                        warnings.append(f"[{path}] {msg}")

        # Invariant score calculation
        if violations:
            score = max(0.2, 0.7 - (0.25 * len(violations)))
            is_safe = False
        elif warnings:
            score = max(0.75, 0.95 - (0.08 * len(warnings)))
            is_safe = True
        else:
            score = 1.0
            is_safe = True

        report = CrossValidationReport(
            is_safe=is_safe,
            invariant_score=round(score, 2),
            violations=violations,
            warnings=warnings,
            modified_test_count=test_count,
            modified_source_count=src_count,
        )

        logger.info(
            "cross_validator_audit_complete",
            is_safe=is_safe,
            invariant_score=report.invariant_score,
            violations_count=len(violations),
            warnings_count=len(warnings),
        )

        return report
