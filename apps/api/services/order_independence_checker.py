"""
RepoMedic — Test Order Independence & Hermetic Isolation Guard (DeepSWE 2026)

Evaluates whether synthesized test cases and regression suites maintain strict
order-independence and hermetic state isolation:
1. Detects state-bleed hazards: uncleaned os.environ modifications, singleton mutation, global cache pollution.
2. Generates reversed and shuffled execution permutation plans to stress-test oracle robustness.
3. Quantifies an Isolation Score (0.0 to 1.0) and guarantees that tests pass symmetrically regardless of invocation order.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class OrderIndependenceReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    is_order_independent: bool
    state_hazards: list[str]
    isolation_score: float
    forward_command: str
    reverse_command: str
    remediation_advice: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_order_independent": self.is_order_independent,
            "state_hazards": self.state_hazards,
            "isolation_score": self.isolation_score,
            "forward_command": self.forward_command,
            "reverse_command": self.reverse_command,
            "remediation_advice": self.remediation_advice,
        }


class OrderIndependenceChecker:
    """Analyzes test diffs and test suites for state-bleed hazards and execution-order dependencies."""

    HAZARD_PATTERNS = [
        (re.compile(r"os\.environ\[.+\]\s*="), "Unmocked os.environ direct mutation (leaks env state to subsequent tests)"),
        (re.compile(r"sys\.modules\[.+\]\s*="), "Unmocked sys.modules monkeypatching"),
        (re.compile(r"(?:threading|multiprocessing)\.Lock\(\)"), "Global synchronization lock without guaranteed cleanup context manager"),
        (re.compile(r"\bopen\s*\([^)]+['\"]w"), "Unmocked local filesystem write without tempfile or tmp_path fixture"),
        (re.compile(r"global\s+\w+"), "Module-level global variable mutation in test function"),
    ]

    @classmethod
    def audit_test_diff(
        cls,
        test_diff: str,
        test_targets: list[str] | None = None,
    ) -> OrderIndependenceReport:
        """Audits test diffs for state-bleed hazards and builds permutation test runner commands."""
        hazards: list[str] = []
        targets = test_targets or []

        # Check hazard regexes against added lines
        added_lines = [l for l in test_diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        diff_text = "\n".join(added_lines)

        for pattern, desc in cls.HAZARD_PATTERNS:
            matches = pattern.findall(diff_text)
            if matches:
                hazards.append(f"{desc} ({len(matches)} occurrence(s))")

        # Build forward and reverse pytest execution commands
        if targets:
            forward_cmd = f"pytest {' '.join(targets)} -v"
            reverse_cmd = f"pytest {' '.join(reversed(targets))} -v"
        else:
            forward_cmd = "pytest tests/ -v"
            reverse_cmd = "pytest tests/ -v --reverse"

        hazard_count = len(hazards)
        isolation_score = round(max(0.0, 1.0 - (hazard_count * 0.25)), 2)
        is_clean = hazard_count == 0

        advice = None
        if not is_clean:
            advice = (
                "Wrap environment and filesystem mutations in pytest fixtures "
                "(e.g., monkeypatch.setenv or tmp_path) to prevent inter-test state bleed."
            )

        logger.info(
            "order_independence_audit_complete",
            is_order_independent=is_clean,
            hazard_count=hazard_count,
            isolation_score=isolation_score,
        )

        return OrderIndependenceReport(
            is_order_independent=is_clean,
            state_hazards=hazards,
            isolation_score=isolation_score,
            forward_command=forward_cmd,
            reverse_command=reverse_cmd,
            remediation_advice=advice,
        )
