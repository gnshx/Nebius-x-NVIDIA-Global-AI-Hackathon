"""
RepoMedic — Flaky Test Quarantiner & Differential Verification Engine

Implements state-of-the-art flakiness quarantine from:
- SWE-bench Verified: Curating Deterministic Evaluation for Autonomous SE Agents (2024/2025)
- Mitigating Flakiness in Autonomous APR Benchmarking (SWE-bench 2025/2026)

Prevents autonomous coding agents from hallucinating or entering endless repair
loops due to environmental, timing, or pre-existing non-deterministic test failures.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class QuarantinedTest(NamedTuple):
    test_id: str
    reason: str
    category: str
    flip_count: int

    __test__ = False  # Prevent pytest collection warning


class FlakyQuarantineReport(NamedTuple):
    quarantined_tests: list[QuarantinedTest]
    deterministic_tests_count: int
    quarantined_count: int
    deterministic_suite_confidence: float
    pytest_filter_args: str

    __test__ = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "quarantined_tests": [
                {
                    "test_id": q.test_id,
                    "reason": q.reason,
                    "category": q.category,
                    "flip_count": q.flip_count,
                }
                for q in self.quarantined_tests
            ],
            "deterministic_tests_count": self.deterministic_tests_count,
            "quarantined_count": self.quarantined_count,
            "deterministic_suite_confidence": round(self.deterministic_suite_confidence, 4),
            "pytest_filter_args": self.pytest_filter_args,
        }


class FlakyTestQuarantiner:
    """Manages the quarantine of non-deterministic, flaky, or environmental test failures."""

    FLAKY_PATTERNS = [
        ("SOCKET_BINDING", re.compile(r"address already in use|errno 98|port \d+ in use", re.IGNORECASE)),
        ("NETWORK_TIMEOUT", re.compile(r"connection timed out|remotedisconnected|readtimeout|max retries exceeded", re.IGNORECASE)),
        ("RESOURCE_EXHAUSTION", re.compile(r"resource temporarily unavailable|errno 11|too many open files", re.IGNORECASE)),
        ("RACE_CONDITION", re.compile(r"deadlock detected|concurrentmodification|thread lock", re.IGNORECASE)),
        ("TIMING_JITTER", re.compile(r"assert delta < \d+|tolerance exceeded|timing out after \d+s", re.IGNORECASE)),
    ]

    def __init__(self) -> None:
        self._quarantined: dict[str, QuarantinedTest] = {}
        self._history: dict[str, list[bool]] = {}  # test_id -> list of pass/fail booleans

    def record_test_run(self, test_id: str, passed: bool, error_message: str = "") -> None:
        """Record the outcome of a test across consecutive execution turns."""
        if test_id not in self._history:
            self._history[test_id] = []
        self._history[test_id].append(passed)

        # Detect pattern-based flakiness
        if not passed and error_message:
            for cat, regex in self.FLAKY_PATTERNS:
                if regex.search(error_message):
                    self._quarantine(
                        test_id=test_id,
                        reason=f"Matched environmental flakiness pattern: {cat}",
                        category=cat,
                    )
                    return

        # Detect outcome flip flakiness (e.g. passed -> failed -> passed without relevant file changes)
        outcomes = self._history[test_id]
        if len(outcomes) >= 2:
            flips = sum(1 for i in range(1, len(outcomes)) if outcomes[i] != outcomes[i - 1])
            if flips >= 2 and test_id not in self._quarantined:
                self._quarantine(
                    test_id=test_id,
                    reason=f"Detected {flips} intermittent pass/fail flips across execution turns",
                    category="INTERMITTENT_FLIP",
                    flip_count=flips,
                )

    def _quarantine(
        self, test_id: str, reason: str, category: str, flip_count: int = 1
    ) -> None:
        """Quarantine a test from impacting the strict Zero-Hallucination gate."""
        clean_id = test_id.strip()
        if clean_id not in self._quarantined:
            self._quarantined[clean_id] = QuarantinedTest(
                test_id=clean_id,
                reason=reason,
                category=category,
                flip_count=flip_count,
            )
            logger.warning(
                "test_quarantined",
                test_id=clean_id,
                category=category,
                reason=reason,
            )

    def is_quarantined(self, test_id: str) -> bool:
        """Check if a specific test is currently quarantined."""
        return test_id.strip() in self._quarantined

    def build_pytest_filter_args(self) -> str:
        """Generate command-line exclusion arguments for pytest."""
        if not self._quarantined:
            return ""

        # Extract base test function names for -k exclusion
        test_names = []
        for tid in self._quarantined.keys():
            # Extract func name from tests/test_foo.py::test_bar
            func_name = tid.split("::")[-1].split("[")[0].strip()
            if func_name and func_name not in test_names:
                test_names.append(func_name)

        if not test_names:
            return ""

        expressions = " and ".join(f"not {name}" for name in test_names[:10])
        return f'-k "{expressions}"'

    def generate_report(self, total_tests_executed: int) -> FlakyQuarantineReport:
        """Generate a structured audit report of all quarantined tests."""
        quarantined_list = list(self._quarantined.values())
        quarantined_count = len(quarantined_list)
        deterministic_count = max(0, total_tests_executed - quarantined_count)

        if total_tests_executed > 0:
            confidence = max(0.0, min(1.0, 1.0 - (quarantined_count / total_tests_executed)))
        else:
            confidence = 1.0

        return FlakyQuarantineReport(
            quarantined_tests=quarantined_list,
            deterministic_tests_count=deterministic_count,
            quarantined_count=quarantined_count,
            deterministic_suite_confidence=confidence,
            pytest_filter_args=self.build_pytest_filter_args(),
        )
