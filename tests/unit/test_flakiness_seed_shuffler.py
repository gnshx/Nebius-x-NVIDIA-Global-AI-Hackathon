"""Unit tests for Automated Flakiness Multi-Seed Shuffler (DeepSWE / SWE-bench 2026)."""

import pytest
from services.flakiness_seed_shuffler import (
    FlakinessSeedShuffler,
    FlakinessAuditReport,
    ShuffleTrial,
)


def test_shuffler_deterministic_suite():
    def mock_runner(seed: int, is_reversed: bool):
        return True, []

    report = FlakinessSeedShuffler.evaluate(mock_runner, seeds=[42, 100, 2026])
    assert report.is_deterministic is True
    assert report.stability_score == 1.0
    assert len(report.flaky_tests) == 0
    assert report.total_trials == 6
    assert "Deterministic patch verified" in report.recommendation


def test_shuffler_deterministic_failing_suite():
    def mock_runner(seed: int, is_reversed: bool):
        return False, ["test_calc_error"]

    report = FlakinessSeedShuffler.evaluate(mock_runner, seeds=[1, 2])
    assert report.is_deterministic is True
    assert report.stability_score == 1.0
    assert len(report.flaky_tests) == 0
    assert report.total_trials == 4


def test_shuffler_flaky_suite():
    def mock_runner(seed: int, is_reversed: bool):
        if seed == 1337:
            return False, ["test_race_condition"]
        return True, []

    report = FlakinessSeedShuffler.evaluate(mock_runner, seeds=[42, 1337])
    assert report.is_deterministic is False
    assert report.stability_score < 1.0
    assert "test_race_condition" in report.flaky_tests
    assert "Stochastic flakiness detected" in report.recommendation


def test_shuffler_order_dependent_suite():
    def mock_runner(seed: int, is_reversed: bool):
        if is_reversed:
            return False, ["test_state_bleed"]
        return True, []

    report = FlakinessSeedShuffler.evaluate(mock_runner, seeds=[42])
    assert report.is_deterministic is False
    assert "test_state_bleed" in report.flaky_tests


def test_shuffler_execution_exception_handled():
    def exploding_runner(seed: int, is_reversed: bool):
        if seed == 999:
            raise RuntimeError("Container socket timeout")
        return True, []

    report = FlakinessSeedShuffler.evaluate(exploding_runner, seeds=[42, 999])
    assert report.total_trials == 4
    assert any("execution_error" in t for t in report.flaky_tests)


def test_shuffler_audit_test_result_passed():
    test_result = {
        "success": True,
        "tests_passed": 15,
        "tests_failed": 0,
        "failing_tests": [],
        "stdout": "15 passed in 0.22s",
        "stderr": "",
    }
    report = FlakinessSeedShuffler.audit_test_result(test_result)
    assert report.is_deterministic is True
    assert report.stability_score == 1.0
    assert len(report.flaky_tests) == 0


def test_shuffler_audit_test_result_with_flaky_marker():
    test_result = {
        "success": False,
        "tests_passed": 14,
        "tests_failed": 1,
        "failing_tests": [{"name": "test_dict_order", "message": "AssertionError: Lists differ: [1, 2] != [2, 1]"}],
        "stdout": "FAILED test_dict_order - AssertionError: Lists differ: [",
        "stderr": "",
    }
    report = FlakinessSeedShuffler.audit_test_result(test_result)
    assert report.is_deterministic is False
    assert "test_dict_order" in report.flaky_tests
    assert report.stability_score == 0.5



def test_audit_test_result_clean():
    clean_result = {"success": True, "tests_passed": 5, "tests_failed": 0, "failing_tests": []}
    report = FlakinessSeedShuffler.audit_test_result(clean_result)
    assert report.is_deterministic is True
    assert report.stability_score == 1.0
    assert len(report.flaky_tests) == 0


def test_audit_test_result_suspicious():
    suspicious_result = {
        "success": False,
        "tests_passed": 4,
        "tests_failed": 1,
        "failing_tests": [{"name": "test_ordering"}],
        "stdout": "AssertionError: Lists differ: [1, 2] != [2, 1]",
    }
    report = FlakinessSeedShuffler.audit_test_result(suspicious_result)
    assert report.is_deterministic is False
    assert report.stability_score < 1.0
    assert "test_ordering" in report.flaky_tests

