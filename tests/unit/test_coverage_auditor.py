"""
Unit tests for CoverageTraceAuditor (SWE-ABS 2026).
"""

import pytest
from services.coverage_auditor import CoverageTraceAuditor, CoverageVerdict


SAMPLE_PATCH = """
--- a/src/humanize/number.py
+++ b/src/humanize/number.py
@@ -54,6 +54,9 @@ def intcomma(value, ndigits=None):
+    if ndigits is not None and ndigits < 0:
+        raise ValueError("ndigits must be non-negative")
"""


def test_coverage_trace_exercised():
    test_output = """
    rootdir: /workspace/humanize
    collected 241 items
    tests/test_number.py::test_intcomma PASSED [ 24%]
    tests/test_number.py::test_intcomma_negative_ndigits PASSED [ 25%]
    ======================== 241 passed in 0.20s ===========================
    """
    report = CoverageTraceAuditor.audit_trace(
        patch_diff=SAMPLE_PATCH,
        test_output=test_output,
        modified_files=["src/humanize/number.py"],
    )

    assert report.verdict == CoverageVerdict.EXERCISED
    assert "src/humanize/number.py" in report.target_files_detected
    assert "intcomma" in report.symbols_exercised
    assert not report.is_vacuous_pass
    assert report.confidence_score >= 0.85


def test_coverage_trace_bypassed_vacuous():
    test_output = """
    rootdir: /workspace/humanize
    collected 10 items
    tests/test_filesize.py::test_naturalsize PASSED [ 50%]
    tests/test_time.py::test_naturaltime PASSED [100%]
    ======================== 10 passed in 0.05s ===========================
    """
    report = CoverageTraceAuditor.audit_trace(
        patch_diff=SAMPLE_PATCH,
        test_output=test_output,
        modified_files=["src/humanize/number.py"],
    )

    assert report.verdict == CoverageVerdict.BYPASSED
    assert report.is_vacuous_pass
    assert report.confidence_score < 0.30
    assert "Vacuous Test Execution Warning" in report.details


def test_coverage_trace_inconclusive_empty():
    report = CoverageTraceAuditor.audit_trace(
        patch_diff="",
        test_output="all passed",
        modified_files=[],
    )

    assert report.verdict == CoverageVerdict.INCONCLUSIVE
    assert report.confidence_score == 0.5


def test_coverage_audit_report_serialization():
    report = CoverageTraceAuditor.audit_trace(
        patch_diff=SAMPLE_PATCH,
        test_output="src/humanize/number.py passed",
        modified_files=["src/humanize/number.py"],
    )
    d = report.to_dict()
    assert "verdict" in d
    assert "confidence_score" in d
    assert "is_vacuous_pass" in d
