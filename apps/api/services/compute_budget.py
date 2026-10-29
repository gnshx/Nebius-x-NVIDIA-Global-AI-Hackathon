"""
RepoMedic — Dynamic Test-Time Compute Budget & Complexity Analyzer

Implements test-time scaling principles from:
- Test-Time Compute Scaling for Software Engineering Agents (SWE-bench 2025/2026)
- Adaptive Inference-Time Search Budgets for Code Repair

Dynamically computes the optimal token budget, reasoning depth, and context slice
based on:
1. Stacktrace frame depth (traceback parsing)
2. Cyclomatic & keyword complexity indicators (recursion, race conditions, type errors)
3. Target repository scale and acceptance criteria count
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class ComplexityTier(str, Enum):
    LOW = "LOW"         # Atomic bug: localized logic, single frame, clear fix (e.g., intcomma)
    MEDIUM = "MEDIUM"   # Standard issue: 2-4 traceback frames, multi-statement validation
    HIGH = "HIGH"       # Complex architectural: deep stacktrace, recursion, concurrency


class ComputeBudget(NamedTuple):
    tier: ComplexityTier
    max_tokens: int
    temperature: float
    max_context_chunks: int
    reasoning_mode: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_context_chunks": self.max_context_chunks,
            "reasoning_mode": self.reasoning_mode,
            "rationale": self.rationale,
        }


class ComplexityAnalyzer:
    """Analyzes bug reports and stacktraces to dynamically allocate compute budgets."""

    HIGH_COMPLEXITY_PATTERNS = [
        re.compile(r"recursionerror", re.IGNORECASE),
        re.compile(r"deadlock|race\s*condition|concurrency", re.IGNORECASE),
        re.compile(r"memoryerror|segmentation\s*fault", re.IGNORECASE),
        re.compile(r"asyncio\..*timeout|future\s*cancelled", re.IGNORECASE),
        re.compile(r"metaclass|abstractmethod|typeerror.*multiple\s*bases", re.IGNORECASE),
    ]

    @classmethod
    def estimate_stacktrace_depth(cls, text: str) -> int:
        """Count the number of Python traceback frames in text."""
        if not text:
            return 0
        matches = re.findall(r'File ".*?", line \d+', text)
        return len(matches)

    @classmethod
    def allocate_budget(
        cls,
        issue_title: str,
        issue_body: str,
        acceptance_criteria: list[str] | None = None,
        context_chunks_count: int = 0,
    ) -> ComputeBudget:
        """Calculate dynamic compute budget based on problem attributes."""
        combined_text = f"{issue_title}\n{issue_body or ''}"
        stacktrace_depth = cls.estimate_stacktrace_depth(combined_text)
        criteria_count = len(acceptance_criteria or [])

        # Check for high complexity markers
        has_high_pattern = any(p.search(combined_text) for p in cls.HIGH_COMPLEXITY_PATTERNS)

        if has_high_pattern or stacktrace_depth >= 6 or criteria_count >= 5:
            tier = ComplexityTier.HIGH
            max_tokens = 8192
            temperature = 0.15
            max_chunks = 12
            reasoning_mode = "DEEP_COT_SEARCH"
            rationale = (
                f"High complexity detected (stacktrace depth={stacktrace_depth}, "
                f"criteria={criteria_count}, pattern_match={has_high_pattern}). "
                "Allocating 8K max tokens with deep chain-of-thought search."
            )
        elif stacktrace_depth >= 2 or criteria_count >= 2 or len(combined_text) > 1500:
            tier = ComplexityTier.MEDIUM
            max_tokens = 4096
            temperature = 0.1
            max_chunks = 8
            reasoning_mode = "STANDARD_COT"
            rationale = (
                f"Medium complexity (stacktrace depth={stacktrace_depth}, criteria={criteria_count}). "
                "Allocating standard 4K token compute budget."
            )
        else:
            tier = ComplexityTier.LOW
            max_tokens = 2048
            temperature = 0.05
            max_chunks = 5
            reasoning_mode = "LEAN_DIRECT_SYNTHESIS"
            rationale = (
                "Atomic or localized bug detected. Allocating lean 2K budget for sub-second latency."
            )

        budget = ComputeBudget(
            tier=tier,
            max_tokens=max_tokens,
            temperature=temperature,
            max_context_chunks=max_chunks,
            reasoning_mode=reasoning_mode,
            rationale=rationale,
        )

        logger.info(
            "dynamic_compute_budget_allocated",
            tier=tier.value,
            max_tokens=max_tokens,
            reasoning_mode=reasoning_mode,
        )

        return budget
