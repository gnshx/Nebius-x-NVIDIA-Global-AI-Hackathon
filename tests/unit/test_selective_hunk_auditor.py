"""Unit tests for SelectiveHunkAuditor (CodeMonkeys / DeepSWE 2026)."""

import pytest
from services.selective_hunk_auditor import SelectiveHunkAuditor, HunkAuditReport, HunkMetadata


def test_selective_hunk_auditor_semantic_logic():
    diff = (
        "--- a/src/math.py\n"
        "+++ b/src/math.py\n"
        "@@ -10,3 +10,5 @@\n"
        " def calc(val):\n"
        "+    if val < 0:\n"
        "+        raise ValueError('Must be non-negative')\n"
        "     return val * 2\n"
    )

    report = SelectiveHunkAuditor.audit_and_stage_diff(diff, "src/math.py")
    assert isinstance(report, HunkAuditReport)
    assert report.total_hunks == 1
    assert report.essential_hunks == 1
    assert report.cosmetic_hunks == 0
    assert report.parsimony_ratio == 1.0
    assert "raise ValueError" in report.staged_diff


def test_selective_hunk_auditor_filters_whitespace_churn():
    diff = (
        "--- a/src/utils.py\n"
        "+++ b/src/utils.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-def helper():\n"
        "+def helper():  \n"
        "     pass\n"
        "@@ -20,3 +20,5 @@\n"
        " def real_func(x):\n"
        "+    x += 1\n"
        "+    return x\n"
        "     return 0\n"
    )

    report = SelectiveHunkAuditor.audit_and_stage_diff(diff, "src/utils.py")
    assert report.total_hunks == 2
    assert report.essential_hunks == 1
    assert report.cosmetic_hunks == 1
    assert report.hunk_details[0].category == "COSMETIC_WHITESPACE"
    assert report.hunk_details[1].category == "SEMANTIC_LOGIC"
    # Cosmetic hunk was pruned from staged diff
    assert "real_func" in report.staged_diff
    assert "helper():  " not in report.staged_diff


def test_selective_hunk_auditor_comment_only():
    diff = (
        "--- a/src/core.py\n"
        "+++ b/src/core.py\n"
        "@@ -5,3 +5,3 @@\n"
        "-# old comment\n"
        "+# new comment\n"
        " def run(): pass\n"
    )

    report = SelectiveHunkAuditor.audit_and_stage_diff(diff, "src/core.py")
    assert report.total_hunks == 1
    assert report.essential_hunks == 0
    assert report.cosmetic_hunks == 1
    assert report.hunk_details[0].category == "COMMENT_ONLY"
    assert report.staged_diff == ""


def test_selective_hunk_auditor_import_statement():
    diff = (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+import math\n"
        " import os\n"
    )

    report = SelectiveHunkAuditor.audit_and_stage_diff(diff, "src/app.py")
    assert report.total_hunks == 1
    assert report.essential_hunks == 1
    assert report.hunk_details[0].category == "IMPORT_STATEMENT"
    assert "import math" in report.staged_diff


def test_selective_hunk_auditor_empty():
    report = SelectiveHunkAuditor.audit_and_stage_diff("", "")
    assert report.total_hunks == 0
    assert report.staged_diff == ""
    d = report.to_dict()
    assert isinstance(d, dict)
    assert d["parsimony_ratio"] == 1.0
