"""
Unit tests for pytest output parser.

Tests both JSON report format and plain text fallback.
"""
from __future__ import annotations

import pytest

from services.test_parser import TestResultParser


@pytest.fixture
def parser():
    return TestResultParser()


class TestJsonReportParsing:
    """Tests for --json-report JSON format parsing."""

    def test_all_passed(self, parser):
        stdout = '{"summary": {"passed": 47, "total": 47}, "tests": []}'
        result = parser.parse(exit_code=0, stdout=stdout, stderr="", duration_seconds=3.2)
        assert result.success is True
        assert result.tests_passed == 47
        assert result.tests_failed == 0
        assert result.tests_total == 47

    def test_some_failed(self, parser):
        stdout = """\
{"summary": {"passed": 10, "failed": 2, "total": 12}, "tests": [
  {"nodeid": "tests/test_utils.py::test_parse_user_id", "outcome": "failed",
   "call": {"longrepr": "AssertionError: assert 1 == 123"}},
  {"nodeid": "tests/test_utils.py::test_roundtrip", "outcome": "failed",
   "call": {"longrepr": "IndexError: list index out of range"}}
]}"""
        result = parser.parse(exit_code=1, stdout=stdout, stderr="", duration_seconds=5.1)
        assert result.success is False
        assert result.exit_code == 1
        assert result.tests_passed == 10
        assert result.tests_failed == 2
        assert len(result.failing_tests) == 2
        assert result.failing_tests[0].name == "tests/test_utils.py::test_parse_user_id"
        assert "AssertionError" in result.failing_tests[0].error_type

    def test_failure_summary_generated(self, parser):
        stdout = """\
{"summary": {"passed": 5, "failed": 1, "total": 6}, "tests": [
  {"nodeid": "test_foo", "outcome": "failed", "call": {"longrepr": "AssertionError: foo"}}
]}"""
        result = parser.parse(exit_code=1, stdout=stdout, stderr="", duration_seconds=1.0)
        assert result.failure_summary is not None
        assert "test_foo" in result.failure_summary


class TestTextParsing:
    """Tests for plain text pytest output parsing (fallback)."""

    SAMPLE_PASS_OUTPUT = """\
collected 47 items

tests/test_utils.py .........................................         [100%]

========================= 47 passed in 3.21s ==========================
"""

    SAMPLE_FAIL_OUTPUT = """\
collected 12 items

tests/test_utils.py ..........FF                                      [100%]

================================ FAILURES ================================
___________________ TestParseUserId.test_basic_parse ___________________
AssertionError: assert IndexError was raised

FAILED tests/test_utils.py::TestParseUserId::test_basic_parse - AssertionError
FAILED tests/test_utils.py::TestParseUserId::test_roundtrip - IndexError

================ 10 passed, 2 failed in 5.14s ============================
"""

    def test_all_passed_text(self, parser):
        result = parser.parse(
            exit_code=0,
            stdout=self.SAMPLE_PASS_OUTPUT,
            stderr="",
            duration_seconds=3.21,
        )
        assert result.success is True
        assert result.tests_passed == 47
        assert result.tests_failed == 0

    def test_some_failed_text(self, parser):
        result = parser.parse(
            exit_code=1,
            stdout=self.SAMPLE_FAIL_OUTPUT,
            stderr="",
            duration_seconds=5.14,
        )
        assert result.success is False
        assert result.tests_passed == 10
        assert result.tests_failed == 2
        assert len(result.failing_tests) == 2

    def test_exit_code_zero_means_success(self, parser):
        result = parser.parse(exit_code=0, stdout="", stderr="", duration_seconds=0.1)
        assert result.success is True

    def test_exit_code_nonzero_means_failure(self, parser):
        result = parser.parse(exit_code=1, stdout="", stderr="error", duration_seconds=0.1)
        assert result.success is False


class TestErrorTypeExtraction:
    """Tests for error type extraction from tracebacks."""

    def test_assertion_error(self, parser):
        text = "AssertionError: assert 1 == 2"
        error_type = parser._extract_error_type(text)
        assert error_type == "AssertionError"

    def test_import_error(self, parser):
        text = "ImportError: No module named 'mylib'"
        error_type = parser._extract_error_type(text)
        assert error_type == "ImportError"

    def test_index_error(self, parser):
        text = "IndexError: list index out of range"
        error_type = parser._extract_error_type(text)
        assert error_type == "IndexError"

    def test_unknown_error(self, parser):
        text = "Something went wrong"
        error_type = parser._extract_error_type(text)
        assert error_type == "UnknownError"
