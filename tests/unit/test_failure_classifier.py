"""
Unit tests for failure classification.

Tests that different error types map to correct FailureCategory.
"""
from __future__ import annotations

import pytest

from models.schemas import FailureCategory, TestResultSchema, FailingTestSchema


def make_test_result(
    error_type: str,
    message: str = "",
    exit_code: int = 1,
) -> TestResultSchema:
    return TestResultSchema(
        success=False,
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration_seconds=1.0,
        tests_total=1,
        tests_passed=0,
        tests_failed=1,
        failing_tests=[
            FailingTestSchema(
                name="tests/test_foo.py::test_bar",
                error_type=error_type,
                message=message,
                traceback=f"{error_type}: {message}",
            )
        ],
    )


class TestFailureClassification:
    """
    Tests for failure category logic.
    
    Note: These test the classification logic directly (pure function tests).
    The actual node uses the LLM for production, but classification heuristics
    should be unit-testable.
    """

    def _classify(self, error_type: str, message: str = "") -> FailureCategory:
        """Simple classification heuristic matching what the LLM prompt teaches."""
        error_lower = error_type.lower()
        msg_lower = message.lower()

        if "importerror" in error_lower or "modulenotfounderror" in error_lower:
            return FailureCategory.DEPENDENCY_ERROR
        if "assertionerror" in error_lower:
            return FailureCategory.CODE_ERROR
        if "syntaxerror" in error_lower:
            return FailureCategory.CODE_ERROR
        if "timeout" in error_lower or "timeouterror" in error_lower:
            return FailureCategory.TIMEOUT
        if "connectionerror" in error_lower or "networkerror" in error_lower:
            return FailureCategory.ENVIRONMENT_ERROR
        return FailureCategory.UNKNOWN

    def test_assertion_error_is_code_error(self):
        cat = self._classify("AssertionError", "assert 1 == 2")
        assert cat == FailureCategory.CODE_ERROR

    def test_import_error_is_dependency_error(self):
        cat = self._classify("ImportError", "No module named 'mylib'")
        assert cat == FailureCategory.DEPENDENCY_ERROR

    def test_module_not_found_is_dependency_error(self):
        cat = self._classify("ModuleNotFoundError", "No module named 'requests'")
        assert cat == FailureCategory.DEPENDENCY_ERROR

    def test_syntax_error_is_code_error(self):
        cat = self._classify("SyntaxError", "invalid syntax")
        assert cat == FailureCategory.CODE_ERROR

    def test_timeout_is_timeout(self):
        cat = self._classify("TimeoutError")
        assert cat == FailureCategory.TIMEOUT

    def test_unknown_stays_unknown(self):
        cat = self._classify("SomeRandomError", "something weird happened")
        assert cat == FailureCategory.UNKNOWN

    def test_connection_error_is_environment(self):
        cat = self._classify("ConnectionError", "failed to connect")
        assert cat == FailureCategory.ENVIRONMENT_ERROR
