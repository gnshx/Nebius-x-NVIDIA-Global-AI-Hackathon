"""
RepoMedic — Context-Aware Dynamic Sampling & Reasoning Budget Adapter

Implements test-time compute (TTC) scaling patterns from:
- SWE-Reasoner: Advances in Test-Time Compute for Autonomous Program Repair (2025/2026)
- Agentless & Maestro: Multi-Turn Reasoning Temperature Adaptation

Dynamically calibrates model temperature, top_p, and chain-of-thought reasoning token quotas
based on iteration turn, failure delta verdict, and stacktrace complexity.
"""

from __future__ import annotations

from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class SamplingConfig(NamedTuple):
    temperature: float
    top_p: float
    max_tokens: int
    enable_thinking: bool
    reasoning_budget_tokens: int
    sampling_mode: str
    rationale: str

    __test__ = False  # Prevent pytest collection warning

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "enable_thinking": self.enable_thinking,
            "reasoning_budget_tokens": self.reasoning_budget_tokens,
            "sampling_mode": self.sampling_mode,
            "rationale": self.rationale,
        }


class DynamicSamplingAdapter:
    """Adapts LLM sampling hyperparameters dynamically across agentic repair iterations."""

    @classmethod
    def calibrate(
        cls,
        iteration: int = 0,
        delta_verdict: str | None = None,
        complexity_tier: str | None = None,
    ) -> SamplingConfig:
        """Calculate optimal sampling configuration for the given repair state."""
        tier = (complexity_tier or "STANDARD").upper()
        verdict = (delta_verdict or "INITIAL").upper()

        # Base token allocation
        base_tokens = 4096
        if tier == "HIGH" or tier == "DEEP_TRACE":
            base_tokens = 8192
        elif tier == "LOW" or tier == "ATOMIC":
            base_tokens = 2048

        # Iteration 0: First-Shot Fix (Strict Canonical Generation)
        if iteration == 0:
            return SamplingConfig(
                temperature=0.1,
                top_p=0.95,
                max_tokens=base_tokens,
                enable_thinking=True,
                reasoning_budget_tokens=2048,
                sampling_mode="CANONICAL_DETERMINISTIC",
                rationale="First-shot repair: Low temperature for maximum determinism and standard adherence.",
            )

        # Iteration 1: Targeted Self-Healing
        if iteration == 1:
            if verdict == "IMPROVED":
                return SamplingConfig(
                    temperature=0.2,
                    top_p=0.95,
                    max_tokens=base_tokens,
                    enable_thinking=True,
                    reasoning_budget_tokens=4096,
                    sampling_mode="TARGETED_REFINEMENT",
                    rationale="Progress detected: Conservative temperature focusing strictly on remaining persistent failures.",
                )
            elif verdict == "REGRESSED":
                return SamplingConfig(
                    temperature=0.35,
                    top_p=0.90,
                    max_tokens=base_tokens,
                    enable_thinking=True,
                    reasoning_budget_tokens=6144,
                    sampling_mode="REGRESSION_RECOVERY",
                    rationale="Regression detected: Elevated thinking tokens to analyze why previous patch broke passing tests.",
                )
            else:
                return SamplingConfig(
                    temperature=0.25,
                    top_p=0.95,
                    max_tokens=base_tokens,
                    enable_thinking=True,
                    reasoning_budget_tokens=4096,
                    sampling_mode="ITERATIVE_HEALING",
                    rationale="Unchanged failure: Moderate temperature and expanded reasoning to reconsider root cause.",
                )

        # Iteration 2+: Exploratory Boundary Repair
        return SamplingConfig(
            temperature=0.5,
            top_p=0.85,
            max_tokens=base_tokens,
            enable_thinking=True,
            reasoning_budget_tokens=8192,
            sampling_mode="EXPLORATORY_BOUNDARY",
            rationale="Final fallback turn: Higher temperature and maximum reasoning budget to escape local minima.",
        )
