"""Unit tests for Self-Supervised Dynamic Mock Invariant Synthesizer (ICSE 2026)."""

import pytest
from services.dynamic_mock_synthesizer import (
    DynamicMockSynthesizer,
    ExternalCallSignature,
    HermeticIsolationReport,
)


def test_scan_no_external_io():
    synthesizer = DynamicMockSynthesizer()
    source_code = """
def calculate_factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
"""
    test_code = """
def test_factorial():
    assert calculate_factorial(5) == 120
"""
    report = synthesizer.scan_code_for_external_io(source_code, test_code)
    assert report.is_hermetic_safe is True
    assert report.isolation_score == 1.0
    assert len(report.unmocked_calls) == 0
    assert len(report.mocked_calls) == 0
    assert report.synthesized_harness == ""


def test_scan_unmocked_requests_call():
    synthesizer = DynamicMockSynthesizer()
    source_code = """
import requests

def fetch_issue(repo: str, issue_id: int):
    url = f"https://api.github.com/repos/{repo}/issues/{issue_id}"
    resp = requests.get("https://api.github.com/repos/test/issues/1")
    return resp.json()
"""
    test_code = """
def test_fetch_issue():
    data = fetch_issue("test", 1)
    assert data["status"] == "ok"
"""
    report = synthesizer.scan_code_for_external_io(source_code, test_code)
    assert report.is_hermetic_safe is False
    assert report.isolation_score == 0.0
    assert len(report.unmocked_calls) >= 1
    call = report.unmocked_calls[0]
    assert call.module == "requests"
    assert call.function == "get"
    assert call.inferred_endpoint == "https://api.github.com/repos/test/issues/1"
    assert "patch('requests.get')" in report.synthesized_harness


def test_scan_already_mocked_call():
    synthesizer = DynamicMockSynthesizer()
    source_code = """
import requests

def get_user():
    return requests.get("https://example.com/user")
"""
    test_code = """
from unittest.mock import patch

@patch("requests.get")
def test_get_user(mock_get):
    mock_get.return_value.status_code = 200
    res = get_user()
    assert res.status_code == 200
"""
    report = synthesizer.scan_code_for_external_io(source_code, test_code)
    assert report.is_hermetic_safe is True
    assert report.isolation_score == 1.0
    assert len(report.unmocked_calls) == 0
    assert len(report.mocked_calls) >= 1


def test_synthesize_mock_fixtures_multiple():
    synthesizer = DynamicMockSynthesizer()
    unmocked = [
        ExternalCallSignature(module="requests", function="get", line_number=10),
        ExternalCallSignature(module="httpx", function="post", line_number=25),
    ]
    harness = synthesizer.synthesize_mock_fixtures(unmocked)
    assert "@pytest.fixture(autouse=True)" in harness
    assert "patch('httpx.post')" in harness
    assert "patch('requests.get')" in harness
    assert "MagicMock(status_code=200" in harness


def test_inject_mock_harness_into_test():
    synthesizer = DynamicMockSynthesizer()
    safe_report = HermeticIsolationReport(is_hermetic_safe=True)
    test_code = "def test_ok(): assert True"
    assert synthesizer.inject_mock_harness_into_test(test_code, safe_report) == test_code

    unsafe_report = HermeticIsolationReport(
        is_hermetic_safe=False,
        synthesized_harness="# fixture here",
    )
    injected = synthesizer.inject_mock_harness_into_test(test_code, unsafe_report)
    assert "# fixture here\n\ndef test_ok(): assert True" == injected
