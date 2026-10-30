"""Unit tests for RepoMedic's FailureDistiller service."""

from services.failure_distiller import FailureDistiller


def test_initial_failure_state():
    current_failing = [
        {"name": "tests/test_calc.py::test_div_zero", "error_type": "ZeroDivisionError", "message": "division by zero"}
    ]
    report = FailureDistiller.distill_delta(None, current_failing)

    assert report.delta_verdict == "INITIAL"
    assert len(report.persistent_failures) == 1
    assert len(report.resolved_tests) == 0
    assert len(report.new_regressions) == 0
    assert "Identified 1 failing test(s)" in report.diagnostic_prompt


def test_detects_resolved_failures():
    prev_failing = [
        {"name": "tests/test_a.py::test_1", "error_type": "ValueError", "message": "bad val"},
        {"name": "tests/test_b.py::test_2", "error_type": "KeyError", "message": "missing key"},
    ]
    # Current iteration only has test_2 failing; test_1 was resolved!
    curr_failing = [
        {"name": "tests/test_b.py::test_2", "error_type": "KeyError", "message": "missing key"},
    ]

    report = FailureDistiller.distill_delta(prev_failing, curr_failing)

    assert report.delta_verdict == "IMPROVED"
    assert report.resolved_tests == ["tests/test_a.py::test_1"]
    assert len(report.persistent_failures) == 1
    assert len(report.new_regressions) == 0
    assert report.healing_velocity == 0.5  # 1 net resolved / 2 prev
    assert "Resolved from previous iteration" in report.diagnostic_prompt


def test_detects_new_regressions_and_alerts():
    prev_failing = [
        {"name": "tests/test_a.py::test_1", "error_type": "ValueError", "message": "bad val"},
    ]
    # Current has test_1 still failing PLUS introduced a new regression test_regression!
    curr_failing = [
        {"name": "tests/test_a.py::test_1", "error_type": "ValueError", "message": "bad val"},
        {"name": "tests/test_reg.py::test_break", "error_type": "IndexError", "message": "index out of range"},
    ]

    report = FailureDistiller.distill_delta(prev_failing, curr_failing)

    assert report.delta_verdict == "REGRESSED"
    assert len(report.new_regressions) == 1
    assert report.new_regressions[0]["name"] == "tests/test_reg.py::test_break"
    assert report.healing_velocity == -1.0  # -1 net change / 1 prev
    assert "NEW REGRESSIONS INTRODUCED" in report.diagnostic_prompt


def test_fully_resolved_scenario():
    prev_failing = [
        {"name": "tests/test_a.py::test_1", "error_type": "ValueError", "message": "bad val"},
    ]
    curr_failing = []

    report = FailureDistiller.distill_delta(prev_failing, curr_failing)

    assert report.delta_verdict == "FULLY_RESOLVED"
    assert report.resolved_tests == ["tests/test_a.py::test_1"]
    assert len(report.new_regressions) == 0
    assert len(report.persistent_failures) == 0
    assert report.healing_velocity == 1.0


def test_failure_delta_serialization():
    report = FailureDistiller.distill_delta([], [])
    d = report.to_dict()
    assert "resolved_tests" in d
    assert "new_regressions" in d
    assert "delta_verdict" in d
    assert "healing_velocity" in d
