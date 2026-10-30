"""Unit tests for RepoMedic's AdversarialPreflightAuditor."""

import pytest
from services.preflight_auditor import AdversarialPreflightAuditor, PreflightAuditReport


def test_preflight_clean_patch_passes():
    files = [
        {
            "path": "src/number.py",
            "diff": "@@ -1,3 +1,5 @@\n+    if ndigits < 0:\n+        raise ValueError('negative')",
        }
    ]

    report = AdversarialPreflightAuditor.audit_patch(files)
    assert isinstance(report, PreflightAuditReport)
    assert report.is_sandbox_ready is True
    assert report.risk_level == "LOW"
    assert len(report.issues_detected) == 0
    assert report.clean_lines_ratio == 1.0


def test_preflight_detects_breakpoint_as_high_risk():
    files = [
        {
            "path": "src/debug.py",
            "diff": "@@ -10,2 +10,4 @@\n+    breakpoint()\n+    return result",
        }
    ]

    report = AdversarialPreflightAuditor.audit_patch(files)
    assert report.is_sandbox_ready is False
    assert report.risk_level == "HIGH"
    assert any("breakpoint()" in iss for iss in report.issues_detected)


def test_preflight_detects_pdb_import():
    files = [
        {
            "path": "src/utils.py",
            "diff": "+import pdb; pdb.set_trace()\n",
        }
    ]

    report = AdversarialPreflightAuditor.audit_patch(files)
    assert report.is_sandbox_ready is False
    assert report.risk_level == "HIGH"


def test_preflight_flags_print_in_source_but_allows_in_tests():
    src_files = [{"path": "src/calc.py", "diff": "+    print('debugging')\n"}]
    test_files = [{"path": "tests/test_calc.py", "diff": "+    print('testing')\n"}]

    src_report = AdversarialPreflightAuditor.audit_patch(src_files)
    assert len(src_report.issues_detected) == 1
    assert "print()" in src_report.issues_detected[0]

    test_report = AdversarialPreflightAuditor.audit_patch(test_files)
    assert len(test_report.issues_detected) == 0


def test_preflight_to_dict():
    files = [{"path": "src/a.py", "diff": "+x = 1"}]
    report = AdversarialPreflightAuditor.audit_patch(files)
    d = report.to_dict()

    assert isinstance(d, dict)
    assert "is_sandbox_ready" in d
    assert "risk_level" in d
    assert "clean_lines_ratio" in d
