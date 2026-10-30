"""Unit tests for RepoMedic's TracebackDistiller (RGFL)."""

import pytest
from services.traceback_distiller import TracebackDistiller, DistilledTracebackResult


def test_distill_traceback_isolates_repo_culprit():
    raw_tb = """
Traceback (most recent call last):
  File "/usr/lib/python3.10/unittest/case.py", line 549, in run
    self._callTestMethod(testMethod)
  File "/home/user/.local/lib/python3.10/site-packages/pytest/runner.py", line 120, in pytest_runtest_call
    item.runtest()
  File "/workspace/humanize/tests/test_number.py", line 42, in test_intcomma_negative
    intcomma(1234, ndigits=-1)
  File "/workspace/humanize/src/humanize/number.py", line 58, in intcomma
    return f"{value:.{ndigits}f}"
ValueError: Format specifier missing precision
"""
    result = TracebackDistiller.distill(raw_tb, repo_keywords=["humanize"])

    assert isinstance(result, DistilledTracebackResult)
    assert result.culprit_file == "/workspace/humanize/src/humanize/number.py"
    assert result.culprit_line == 58
    assert result.culprit_function == "intcomma"
    assert result.omitted_frames_count >= 2
    assert "internal runtime" in result.distilled_traceback
    assert "[TARGET REPO]" in result.distilled_traceback
    assert "Crash Exception: ValueError: Format specifier missing precision" in result.distilled_traceback


def test_distill_traceback_empty_or_fallback():
    result = TracebackDistiller.distill("")
    assert result.culprit_file is None
    assert result.omitted_frames_count == 0
    assert result.compression_ratio == 0.0

    non_standard = "Some random error occurred: divide by zero"
    res_non_std = TracebackDistiller.distill(non_standard)
    assert res_non_std.distilled_traceback == non_standard


def test_distill_traceback_to_dict():
    raw_tb = 'File "src/foo.py", line 10, in bar\n    pass'
    result = TracebackDistiller.distill(raw_tb)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "culprit_file" in d
    assert "distilled_traceback" in d
    assert "repo_frames_count" in d
