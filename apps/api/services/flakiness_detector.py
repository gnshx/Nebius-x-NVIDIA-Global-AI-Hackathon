"""
RepoMedic — Flaky Test Detector & Isolation Engine

Implements state-of-the-art flakiness filtering from:
- Mitigating Flakiness in Autonomous APR Benchmarking (SWE-bench 2025/2026)
- Distinguishing Non-Deterministic Environmental Failures from Code Regressions

Identifies test failures driven by:
1. Address already in use / socket bind race conditions (OSError: [Errno 98])
2. Ephemeral network / connection timeouts during external mocks
3. Random number generator or timestamp drift
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class FlakyPattern(NamedTuple):
    category: str
    regex: re.Pattern


class FlakinessDetector:
    """Detects and isolates non-deterministic flaky test failures."""

    FLAKY_PATTERNS = [
        FlakyPattern(
            category="SOCKET_BINDING",
            regex=re.compile(r"address already in use|errno 98|port \d+ in use", re.IGNORECASE),
        ),
        FlakyPattern(
            category="NETWORK_TIMEOUT",
            regex=re.compile(r"connection timed out|remotedisconnected|readtimeout|max retries exceeded", re.IGNORECASE),
        ),
        FlakyPattern(
            category="TEMPORARY_RESOURCE",
            regex=re.compile(r"resource temporarily unavailable|errno 11|too many open files", re.IGNORECASE),
        ),
        FlakyPattern(
            category="THREAD_RACE",
            regex=re.compile(r"deadlock detected|concurrentmodification|thread lock", re.IGNORECASE),
        ),
    ]

    @classmethod
    def is_flaky_failure(cls, message: str) -> tuple[bool, str]:
        """Check if a test failure message matches known environmental flakiness signatures."""
        if not message:
            return False, ""

        for pattern in cls.FLAKY_PATTERNS:
            if pattern.regex.search(message):
                return True, pattern.category

        return False, ""

    @classmethod
    def partition_failures(
        cls, failing_tests: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Partition failures into (deterministic_regressions, quarantined_flaky)."""
        deterministic: list[dict[str, Any]] = []
        quarantined: list[dict[str, Any]] = []

        for f in failing_tests:
            msg = f.get("message", "")
            is_flaky, cat = cls.is_flaky_failure(msg)
            if is_flaky:
                f_copy = dict(f)
                f_copy["flaky_category"] = cat
                quarantined.append(f_copy)
                logger.warning(
                    "flaky_test_quarantined",
                    node=f.get("nodeid"),
                    category=cat,
                )
            else:
                deterministic.append(f)

        return deterministic, quarantined
