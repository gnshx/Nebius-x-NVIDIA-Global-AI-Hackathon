"""Unit tests for Dynamic Compute Budget Allocation & Flakiness Isolation."""

import pytest
from services.compute_budget import ComplexityAnalyzer, ComplexityTier
from services.flakiness_detector import FlakinessDetector


def test_complexity_analyzer_low_atomic_issue():
    budget = ComplexityAnalyzer.allocate_budget(
        issue_title="intcomma() raises ValueError on negative ndigits",
        issue_body="Negative ndigits should raise ValueError('ndigits must be non-negative')",
        acceptance_criteria=["Validate non-negative ndigits"],
    )
    assert budget.tier == ComplexityTier.LOW
    assert budget.max_tokens == 2048
    assert budget.reasoning_mode == "LEAN_DIRECT_SYNTHESIS"


def test_complexity_analyzer_high_traceback_recursion():
    deep_traceback = (
        'File "foo.py", line 10, in a\n'
        'File "foo.py", line 20, in b\n'
        'File "foo.py", line 30, in c\n'
        'File "foo.py", line 40, in d\n'
        'File "foo.py", line 50, in e\n'
        'File "foo.py", line 60, in f\n'
        'File "foo.py", line 70, in g\n'
        "RecursionError: maximum recursion depth exceeded"
    )
    budget = ComplexityAnalyzer.allocate_budget(
        issue_title="Infinite recursion in tree resolution",
        issue_body=deep_traceback,
    )
    assert budget.tier == ComplexityTier.HIGH
    assert budget.max_tokens == 8192
    assert budget.reasoning_mode == "DEEP_COT_SEARCH"


def test_complexity_analyzer_medium():
    traceback = (
        'File "bar.py", line 12, in parse\n'
        'File "bar.py", line 45, in validate\n'
        "ValueError: Invalid value"
    )
    budget = ComplexityAnalyzer.allocate_budget(
        issue_title="Validation error during parse",
        issue_body=traceback,
        acceptance_criteria=["Check empty inputs", "Raise ValueError"],
    )
    assert budget.tier == ComplexityTier.MEDIUM
    assert budget.max_tokens == 4096


def test_flakiness_detector_socket_binding():
    msg = "OSError: [Errno 98] Address already in use"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is True
    assert cat == "SOCKET_BINDING"


def test_flakiness_detector_network_timeout():
    msg = "urllib3.exceptions.MaxRetryError: HTTPSConnectionPool: Connection timed out"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is True
    assert cat == "NETWORK_TIMEOUT"


def test_flakiness_detector_deterministic_failure():
    msg = "AssertionError: assert 12 == 15"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is False
    assert cat == ""


def test_partition_failures():
    failing = [
        {"nodeid": "test_app.py::test_bind", "message": "Address already in use on port 8000"},
        {"nodeid": "test_core.py::test_calc", "message": "AssertionError: assert False"},
        {"nodeid": "test_net.py::test_fetch", "message": "ReadTimeout: connection timed out"},
    ]
    det, quar = FlakinessDetector.partition_failures(failing)
    assert len(det) == 1
    assert det[0]["nodeid"] == "test_core.py::test_calc"
    assert len(quar) == 2
    assert quar[0]["flaky_category"] == "SOCKET_BINDING"
    assert quar[1]["flaky_category"] == "NETWORK_TIMEOUT"
