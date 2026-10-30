"""
RepoMedic — Trajectory Rubric Evaluator (SWE-TRACE 2026)

Inspired by SWE-TRACE (2026): "Optimizing Long-Horizon SWE Agents through
Rubric Process Reward Models and Heuristic Test-Time Scaling".

Implements a Process Reward Model (PRM) rubric evaluator that scores the
multi-turn agent repair trajectory across:
1. Shortest-Path Efficiency: Minimizing extraneous exploration cycles
2. Scope Discipline: Constraining edits strictly to fault-localized boundaries
3. Oracle Monotonicity: Ensuring test improvements are non-regressive
"""

from __future__ import annotations

from enum import Enum
from typing import Any, NamedTuple


class TrajectoryHealth(str, Enum):
    OPTIMAL = "OPTIMAL"         # Shortest path: resolved cleanly without regression
    PROGRESSING = "PROGRESSING" # Progressing: resolving errors with controlled scope
    DIVERGENT = "DIVERGENT"     # Divergent: error count increasing or scope exploding


class TrajectoryRubricReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    health: TrajectoryHealth
    prm_score: float             # Process Reward Model composite score (0.0 - 1.0)
    efficiency_score: float      # Shortest path directness
    scope_discipline_score: float # Adherence to fault localization boundary
    monotonicity_score: float    # Monotonic error reduction
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "health": self.health.value,
            "prm_score": round(self.prm_score, 2),
            "efficiency_score": round(self.efficiency_score, 2),
            "scope_discipline_score": round(self.scope_discipline_score, 2),
            "monotonicity_score": round(self.monotonicity_score, 2),
            "recommendation": self.recommendation,
        }


class TrajectoryRubricEvaluator:
    """Evaluates agent repair trajectories against deterministic PRM rubrics."""

    @classmethod
    def evaluate(
        cls,
        iteration: int,
        failure_counts: list[int] | None = None,
        touched_files: list[str] | None = None,
        localized_files: list[str] | None = None,
    ) -> TrajectoryRubricReport:
        """Computes multi-dimensional PRM rubric scores for the agent trajectory."""
        failure_counts = failure_counts or [0]
        touched_files = touched_files or []
        localized_files = localized_files or []

        # 1. Shortest-Path Efficiency Score
        # Iteration 0: 1.0, Iteration 1: 0.82, Iteration 2: 0.65
        efficiency = max(0.4, 1.0 - (iteration * 0.18))

        # 2. Scope Discipline Score
        if not touched_files or not localized_files:
            scope_score = 1.0
        else:
            localized_set = {f.lower() for f in localized_files}
            touched_set = {f.lower() for f in touched_files}
            in_boundary = touched_set.intersection(localized_set)
            # Penalize touching extraneous files outside fault localization
            scope_score = len(in_boundary) / max(1, len(touched_set))

        # 3. Oracle Monotonicity Score
        if len(failure_counts) <= 1:
            monotonicity = 1.0
        else:
            # Check if errors decreased or stayed zero
            last_err = failure_counts[-1]
            prev_err = failure_counts[-2]
            if last_err == 0:
                monotonicity = 1.0
            elif last_err < prev_err:
                monotonicity = 0.85  # Productive error reduction
            elif last_err == prev_err:
                monotonicity = 0.60  # Stagnant
            else:
                monotonicity = 0.30  # Regression cascade!

        # 4. Composite PRM Score
        # Weighted: 35% Monotonicity, 35% Scope Discipline, 30% Efficiency
        prm_score = (0.35 * monotonicity) + (0.35 * scope_score) + (0.30 * efficiency)

        # 5. Formulate Trajectory Health & Recommendation
        if prm_score >= 0.80 and monotonicity >= 0.80:
            health = TrajectoryHealth.OPTIMAL
            recommendation = "Trajectory is high-efficiency shortest path. Proceed to verification gate."
        elif prm_score >= 0.55:
            health = TrajectoryHealth.PROGRESSING
            recommendation = "Trajectory is progressing with minor overhead. Apply localized test-time compute."
        else:
            health = TrajectoryHealth.DIVERGENT
            recommendation = "Trajectory is divergent. Roll back intermediate patch and re-localize fault slice."

        return TrajectoryRubricReport(
            health=health,
            prm_score=prm_score,
            efficiency_score=efficiency,
            scope_discipline_score=scope_score,
            monotonicity_score=monotonicity,
            recommendation=recommendation,
        )
