"""Unit tests for FlakinessDetector."""

import pytest
from services.flakiness_detector import FlakinessDetector


def test_socket_binding_flakiness():
    msg = "OSError: [Errno 98] Address already in use: 0.0.0.0:8000"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is True
    assert cat == "SOCKET_BINDING"


def test_network_timeout_flakiness():
    msg = "urllib3.exceptions.MaxRetryError: HTTPSConnectionPool: Connection timed out"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is True
    assert cat == "NETWORK_TIMEOUT"


def test_deterministic_failure_not_flaky():
    msg = "AssertionError: expected '42' but got '43'"
    is_flaky, cat = FlakinessDetector.is_flaky_failure(msg)
    assert is_flaky is False
    assert cat == ""


def test_partition_failures():
    failing_tests = [
        {"nodeid": "tests/test_api.py::test_port", "message": "OSError: [Errno 98] Address already in use"},
        {"nodeid": "tests/test_math.py::test_calc", "message": "AssertionError: 2 != 3"},
    ]
    det, quarantined = FlakinessDetector.partition_failures(failing_tests)
    assert len(det) == 1
    assert det[0]["nodeid"] == "tests/test_math.py::test_calc"
    assert len(quarantined) == 1
    assert quarantined[0]["flaky_category"] == "SOCKET_BINDING"
