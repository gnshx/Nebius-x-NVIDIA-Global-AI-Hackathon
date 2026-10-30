"""
RepoMedic — Adaptive Multi-Turn Failure Distiller

Implements differential failure analysis for self-healing loops:
- Compares failure sets between iteration t-1 and iteration t
- Identifies newly introduced regressions vs. resolved failures vs. persistent bugs
- Synthesizes targeted, low-token diagnostic prompts for LLM self-correction
- Prevents oscillation and regression loops where agents re-break working code
"""

from __future__ import annotations

from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class FailureDeltaReport(NamedTuple):
    resolved_tests: list[str]
    new_regressions: list[dict[str, Any]]
    persistent_failures: list[dict[str, Any]]
    delta_verdict: str  # IMPROVED, REGRESSED, UNCHANGED, INITIAL
    healing_velocity: float
    diagnostic_prompt: str

    __test__ = False  # Prevent pytest collection warning

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved_tests": self.resolved_tests,
            "new_regressions": self.new_regressions,
            "persistent_failures": self.persistent_failures,
            "delta_verdict": self.delta_verdict,
            "healing_velocity": round(self.healing_velocity, 4),
            "diagnostic_prompt": self.diagnostic_prompt,
        }


class FailureDistiller:
    """Calculates the differential delta between successive test execution failures."""

    @classmethod
    def distill_delta(
        cls,
        previous_failing: list[dict[str, Any]] | None,
        current_failing: list[dict[str, Any]] | None,
    ) -> FailureDeltaReport:
        """Compare failure states across iterations to produce actionable self-healing guidance."""
        prev = previous_failing or []
        curr = current_failing or []

        prev_map = {f.get("name", ""): f for f in prev if f.get("name")}
        curr_map = {f.get("name", ""): f for f in curr if f.get("name")}

        prev_names = set(prev_map.keys())
        curr_names = set(curr_map.keys())

        # If this is the initial run (no previous failure history)
        if not prev_names:
            diagnostic = cls._format_initial_prompt(curr)
            return FailureDeltaReport(
                resolved_tests=[],
                new_regressions=[],
                persistent_failures=curr,
                delta_verdict="INITIAL",
                healing_velocity=0.0,
                diagnostic_prompt=diagnostic,
            )

        resolved_names = sorted(list(prev_names - curr_names))
        regression_names = sorted(list(curr_names - prev_names))
        persistent_names = sorted(list(prev_names & curr_names))

        new_regressions = [curr_map[name] for name in regression_names]
        persistent_failures = [curr_map[name] for name in persistent_names]

        # Calculate healing velocity: (resolved - regressions) / prev_total
        net_change = len(resolved_names) - len(regression_names)
        velocity = net_change / max(1, len(prev_names))

        if len(curr_names) == 0:
            verdict = "FULLY_RESOLVED"
        elif net_change > 0:
            verdict = "IMPROVED"
        elif net_change < 0:
            verdict = "REGRESSED"
        else:
            verdict = "UNCHANGED"

        diagnostic = cls._format_delta_prompt(
            resolved_names=resolved_names,
            new_regressions=new_regressions,
            persistent_failures=persistent_failures,
            verdict=verdict,
        )

        return FailureDeltaReport(
            resolved_tests=resolved_names,
            new_regressions=new_regressions,
            persistent_failures=persistent_failures,
            delta_verdict=verdict,
            healing_velocity=velocity,
            diagnostic_prompt=diagnostic,
        )

    @classmethod
    def _format_initial_prompt(cls, failures: list[dict[str, Any]]) -> str:
        lines = ["### Initial Test Failure Analysis"]
        if not failures:
            lines.append("All tests currently pass.")
            return "\n".join(lines)

        lines.append(f"Identified {len(failures)} failing test(s):")
        for f in failures[:8]:
            lines.append(f"- `{f.get('name', 'unknown')}`: {f.get('error_type', 'Error')} ({f.get('message', '')[:100]})")
        return "\n".join(lines)

    @classmethod
    def _format_delta_prompt(
        cls,
        resolved_names: list[str],
        new_regressions: list[dict[str, Any]],
        persistent_failures: list[dict[str, Any]],
        verdict: str,
    ) -> str:
        lines = [f"### Multi-Turn Self-Healing Feedback ({verdict})"]

        if resolved_names:
            lines.append(f"✅ **Resolved from previous iteration ({len(resolved_names)}):**")
            for r in resolved_names[:5]:
                lines.append(f"  - `{r}`")

        if new_regressions:
            lines.append(f"🚨 **NEW REGRESSIONS INTRODUCED ({len(new_regressions)}):**")
            lines.append("  *Crucial: Your latest patch broke code that was previously passing.*")
            for reg in new_regressions[:5]:
                lines.append(f"  - `{reg.get('name')}`: {reg.get('error_type')} — {reg.get('message', '')[:100]}")

        if persistent_failures:
            lines.append(f"🎯 **Persistent Unresolved Failures ({len(persistent_failures)}):**")
            for pf in persistent_failures[:5]:
                lines.append(f"  - `{pf.get('name')}`: {pf.get('error_type')} — {pf.get('message', '')[:100]}")

        lines.append("\n**Guidance:** Preserve changes that resolved previous failures. Target persistent failures and immediately revert unintended side effects.")
        return "\n".join(lines)
