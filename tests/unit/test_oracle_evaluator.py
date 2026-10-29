"""Unit tests for RepoMedic's SWE-bench Dual Oracle Evaluator."""

import pytest
from services.oracle_evaluator import OracleEvaluator, OracleVerdict


def test_oracle_resolved_when_all_pass():
    test_result = {
        "tests_passed": 241,
        "tests_failed": 0,
        "tests_total": 241,
        "success": True,
    }
    generated_tests = [{"path": "tests/test_number.py"}]
    cleanliness = 0.95

    eval_res = OracleEvaluator.evaluate(
        test_result=test_result,
        generated_tests=generated_tests,
        cleanliness_score=cleanliness,
    )

    assert eval_res.verdict == OracleVerdict.RESOLVED
    assert eval_res.fail_to_pass_passed == 1
    assert eval_res.regressions_count == 0
    assert eval_res.pass_to_pass_total == 240
    assert eval_res.pass_to_pass_passed == 240
    assert eval_res.confidence_score >= 0.95
    assert "100% test pass oracle achieved" in eval_res.details


def test_oracle_regression_detected():
    test_result = {
        "tests_passed": 235,
        "tests_failed": 6,
        "tests_total": 241,
        "success": False,
    }
    generated_tests = [{"path": "tests/test_number.py"}]

    eval_res = OracleEvaluator.evaluate(
        test_result=test_result,
        generated_tests=generated_tests,
    )

    assert eval_res.verdict == OracleVerdict.REGRESSION_DETECTED
    assert eval_res.regressions_count == 6
    assert eval_res.confidence_score < 0.60
    assert "failure(s) in regression suite" in eval_res.details


def test_oracle_reproduction_failed():
    test_result = {
        "tests_passed": 0,
        "tests_failed": 4,
        "tests_total": 4,
        "success": False,
    }
    generated_tests = [{"path": "tests/test_fail.py"}]

    eval_res = OracleEvaluator.evaluate(
        test_result=test_result,
        generated_tests=generated_tests,
    )

    assert eval_res.verdict == OracleVerdict.REPRODUCTION_FAILED
    assert eval_res.confidence_score == 0.0
    assert eval_res.fail_to_pass_passed == 0


def test_oracle_inconclusive_empty():
    test_result = {
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_total": 0,
        "success": False,
    }

    eval_res = OracleEvaluator.evaluate(test_result=test_result)
    assert eval_res.verdict == OracleVerdict.INCONCLUSIVE
    assert eval_res.confidence_score == 0.2


def test_oracle_to_dict_serialization():
    test_result = {
        "tests_passed": 16,
        "tests_failed": 0,
        "tests_total": 16,
        "success": True,
    }
    eval_res = OracleEvaluator.evaluate(test_result=test_result, cleanliness_score=0.9)
    d = eval_res.to_dict()

    assert isinstance(d, dict)
    assert d["verdict"] == "RESOLVED"
    assert d["fail_to_pass_count"] == 1
    assert d["cleanliness_score"] == 0.9
    assert d["confidence_score"] > 0.9
