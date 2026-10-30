"""Unit tests for RepoMedic's RuntimeLogPruner (SWE-Pruner)."""

import pytest
from services.log_pruner import RuntimeLogPruner, LogPruningResult


def test_strip_ansi_removes_escape_codes():
    raw = "\x1b[32mPASSED\x1b[0m \x1b[31mFAILED\x1b[0m"
    clean = RuntimeLogPruner.strip_ansi(raw)
    assert clean == "PASSED FAILED"


def test_prune_pytest_output_isolates_failures_and_compresses():
    # Simulate a 240-test suite with 1 failure
    passing_lines = "\n".join(f"tests/test_{i}.py::test_{i} PASSED [ {i % 100}%]" for i in range(50))
    stdout = f"""
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.1.1
rootdir: /workspace/project
{passing_lines}
=================================== FAILURES ===================================
_________________________ test_intcomma_negative _________________________

    def test_intcomma_negative():
>       intcomma(1234, ndigits=-1)
E       ValueError: Format specifier missing precision

src/humanize/number.py:58: ValueError
=========================== short test summary info ============================
FAILED tests/test_number.py::test_intcomma_negative - ValueError: Format specifier missing precision
======================== 1 failed, 50 passed in 0.45s ==========================
"""
    result = RuntimeLogPruner.prune_pytest_output(stdout, stderr="")

    assert isinstance(result, LogPruningResult)
    assert result.compression_ratio > 0.40  # significantly compressed
    assert "ValueError: Format specifier missing precision" in result.pruned_text
    assert "test_intcomma_negative" in result.pruned_text
    assert result.isolated_failure_count >= 1
    assert any("ValueError" in exc for exc in result.root_exceptions)
    # Check that repetitive passing test lines are stripped
    assert "tests/test_0.py::test_0 PASSED" not in result.pruned_text


def test_prune_pytest_output_handles_empty():
    result = RuntimeLogPruner.prune_pytest_output("", "")
    assert result.original_bytes == 0
    assert result.pruned_bytes == 0
    assert result.isolated_failure_count == 0


def test_prune_pytest_output_to_dict():
    stdout = "=== FAILURES ===\nValueError: test error\n=== 1 failed ==="
    result = RuntimeLogPruner.prune_pytest_output(stdout)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "compression_ratio" in d
    assert "pruned_text" in d
    assert "root_exceptions" in d
