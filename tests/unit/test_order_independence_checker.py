"""Unit tests for OrderIndependenceChecker (DeepSWE 2026)."""

import pytest
from services.order_independence_checker import OrderIndependenceChecker, OrderIndependenceReport


def test_order_independence_clean_diff():
    diff = (
        "--- a/tests/test_calc.py\n"
        "+++ b/tests/test_calc.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+def test_add_positive():\n"
        "+    assert add(2, 3) == 5\n"
    )

    report = OrderIndependenceChecker.audit_test_diff(diff, ["tests/test_calc.py::test_add_positive"])
    assert isinstance(report, OrderIndependenceReport)
    assert report.is_order_independent is True
    assert len(report.state_hazards) == 0
    assert report.isolation_score == 1.0
    assert "pytest tests/test_calc.py::test_add_positive -v" == report.forward_command
    assert "pytest tests/test_calc.py::test_add_positive -v" == report.reverse_command
    assert report.remediation_advice is None


def test_order_independence_detects_environ_mutation():
    diff = (
        "--- a/tests/test_env.py\n"
        "+++ b/tests/test_env.py\n"
        "@@ -1,3 +1,5 @@\n"
        "+def test_bad_env():\n"
        "+    os.environ['API_KEY'] = 'fake_key'\n"
    )

    report = OrderIndependenceChecker.audit_test_diff(diff)
    assert report.is_order_independent is False
    assert len(report.state_hazards) == 1
    assert "os.environ" in report.state_hazards[0]
    assert report.isolation_score < 1.0
    assert report.remediation_advice is not None


def test_order_independence_detects_filesystem_write():
    diff = (
        "--- a/tests/test_io.py\n"
        "+++ b/tests/test_io.py\n"
        "@@ -5,3 +5,5 @@\n"
        "+def test_write():\n"
        "+    with open('output.txt', 'w') as f:\n"
        "+        f.write('data')\n"
    )

    report = OrderIndependenceChecker.audit_test_diff(diff)
    assert report.is_order_independent is False
    assert any("filesystem write" in h for h in report.state_hazards)


def test_order_independence_multiple_targets_reversal():
    targets = ["tests/test_a.py", "tests/test_b.py", "tests/test_c.py"]
    report = OrderIndependenceChecker.audit_test_diff("", test_targets=targets)
    assert report.forward_command == "pytest tests/test_a.py tests/test_b.py tests/test_c.py -v"
    assert report.reverse_command == "pytest tests/test_c.py tests/test_b.py tests/test_a.py -v"


def test_order_independence_to_dict():
    report = OrderIndependenceChecker.audit_test_diff("+assert True\n")
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "is_order_independent" in d
    assert "state_hazards" in d
    assert "isolation_score" in d
    assert "forward_command" in d
    assert "reverse_command" in d
