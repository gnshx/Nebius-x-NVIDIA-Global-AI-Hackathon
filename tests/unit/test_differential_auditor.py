"""Unit tests for DifferentialBehaviorAuditor (PatchDiff 2025/2026)."""

import pytest
from services.differential_auditor import DifferentialBehaviorAuditor, DifferentialReport


def test_differential_clean_patch():
    diff = (
        "--- a/src/math.py\n"
        "+++ b/src/math.py\n"
        "@@ -1,3 +1,5 @@\n"
        " def calc(x):\n"
        "+    if x < 0:\n"
        "+        raise ValueError('non-negative required')\n"
        "     return x * 2\n"
    )

    report = DifferentialBehaviorAuditor.audit_patch_diff(diff, "src/math.py")
    assert isinstance(report, DifferentialReport)
    assert report.is_contract_preserved is True
    assert report.behavioral_risk == "LOW"
    assert len(report.detected_drifts) == 0
    assert report.contract_safety_score == 1.0


def test_differential_detects_silent_swallow():
    diff = (
        "--- a/src/handler.py\n"
        "+++ b/src/handler.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+    try:\n"
        "+        do_something()\n"
        "+    except Exception:\n"
        "+        pass\n"
    )

    report = DifferentialBehaviorAuditor.audit_patch_diff(diff, "src/handler.py")
    assert report.is_contract_preserved is False
    assert report.behavioral_risk == "HIGH"
    assert any("Contract Breach" in d for d in report.detected_drifts)
    assert report.contract_safety_score < 1.0


def test_differential_detects_api_signature_mutation():
    diff = (
        "--- a/src/api.py\n"
        "+++ b/src/api.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-def process_data(val, timeout=30, strict=True):\n"
        "+def process_data(val):\n"
    )

    report = DifferentialBehaviorAuditor.audit_patch_diff(diff, "src/api.py")
    assert report.is_contract_preserved is False
    assert any("API Mutation" in d for d in report.detected_drifts)


def test_differential_allows_suppression_in_test_files():
    diff = (
        "--- a/tests/test_mock.py\n"
        "+++ b/tests/test_mock.py\n"
        "@@ -1,3 +1,5 @@\n"
        "+    try: flaky_call()\n"
        "+    except Exception: pass\n"
    )

    report = DifferentialBehaviorAuditor.audit_patch_diff(diff, "tests/test_mock.py")
    assert report.is_contract_preserved is True
    assert report.behavioral_risk == "LOW"


def test_differential_to_dict():
    report = DifferentialBehaviorAuditor.audit_patch_diff("")
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "is_contract_preserved" in d
    assert "behavioral_risk" in d
    assert "contract_safety_score" in d
