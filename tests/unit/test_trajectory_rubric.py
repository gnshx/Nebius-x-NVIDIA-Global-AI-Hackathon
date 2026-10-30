"""
Unit tests for TrajectoryRubricEvaluator (SWE-TRACE 2026).
"""

import pytest
from services.trajectory_rubric import TrajectoryRubricEvaluator, TrajectoryHealth


def test_trajectory_optimal_first_shot():
    report = TrajectoryRubricEvaluator.evaluate(
        iteration=0,
        failure_counts=[0],
        touched_files=["src/humanize/number.py"],
        localized_files=["src/humanize/number.py"],
    )

    assert report.health == TrajectoryHealth.OPTIMAL
    assert report.prm_score >= 0.90
    assert report.efficiency_score == 1.0
    assert report.scope_discipline_score == 1.0
    assert report.monotonicity_score == 1.0


def test_trajectory_progressing_two_turns():
    report = TrajectoryRubricEvaluator.evaluate(
        iteration=1,
        failure_counts=[4, 0],
        touched_files=["src/utils.py"],
        localized_files=["src/utils.py"],
    )

    assert report.health == TrajectoryHealth.OPTIMAL
    assert report.prm_score >= 0.85
    assert report.monotonicity_score == 1.0


def test_trajectory_divergent_regression():
    report = TrajectoryRubricEvaluator.evaluate(
        iteration=2,
        failure_counts=[2, 8],  # Errors increased drastically!
        touched_files=["src/utils.py", "src/auth.py", "config.py"],
        localized_files=["src/utils.py"],
    )

    assert report.health == TrajectoryHealth.DIVERGENT
    assert report.prm_score < 0.55
    assert report.monotonicity_score <= 0.35
    assert "Trajectory is divergent" in report.recommendation


def test_trajectory_scope_discipline_penalty():
    report = TrajectoryRubricEvaluator.evaluate(
        iteration=0,
        failure_counts=[0],
        touched_files=["src/a.py", "src/b.py", "src/c.py", "src/d.py"],
        localized_files=["src/a.py"],
    )

    assert report.scope_discipline_score == 0.25
    assert report.prm_score < 0.85


def test_trajectory_rubric_serialization():
    report = TrajectoryRubricEvaluator.evaluate(
        iteration=0,
        failure_counts=[0],
        touched_files=["src/utils.py"],
        localized_files=["src/utils.py"],
    )
    d = report.to_dict()
    assert "health" in d
    assert "prm_score" in d
    assert "efficiency_score" in d
    assert "recommendation" in d
