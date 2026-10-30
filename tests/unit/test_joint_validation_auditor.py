"""Unit tests for JointValidationAuditor (SWEPatchTest 2026)."""

import pytest
from services.joint_validation_auditor import JointValidationAuditor, JVRAuditReport


def test_jvr_high_fidelity_reproduction():
    diff = (
        "--- a/tests/test_math.py\n"
        "+++ b/tests/test_math.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+def test_negative_input():\n"
        "+    with pytest.raises(ValueError):\n"
        "+        calc(-1)\n"
    )

    report = JointValidationAuditor.evaluate_jvr(diff, expected_failure_type="ValueError", test_passed=True)
    assert isinstance(report, JVRAuditReport)
    assert report.is_jvr_robust is True
    assert report.verdict == "HIGH_FIDELITY"
    assert report.reproduction_fidelity == 1.0
    assert report.positive_conformance == 1.0
    assert report.negative_discrimination == 1.0
    assert report.jvr_score == 1.0


def test_jvr_penalizes_tautology():
    diff = (
        "--- a/tests/test_cheat.py\n"
        "+++ b/tests/test_cheat.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+def test_cheat():\n"
        "+    assert True\n"
    )

    report = JointValidationAuditor.evaluate_jvr(diff, test_passed=True, has_tautologies=True)
    assert report.is_jvr_robust is False
    assert report.verdict == "SUSPECT_ORACLE"
    assert report.negative_discrimination <= 0.2


def test_jvr_penalizes_skip():
    diff = (
        "--- a/tests/test_skip.py\n"
        "+++ b/tests/test_skip.py\n"
        "@@ -1,2 +1,4 @@\n"
        "+@pytest.mark.skip(reason='broken')\n"
        "+def test_skipped():\n"
        "+    assert calc(1) == 2\n"
    )

    report = JointValidationAuditor.evaluate_jvr(diff, test_passed=True)
    assert report.is_jvr_robust is False
    assert report.negative_discrimination == 0.0


def test_jvr_empty_diff():
    report = JointValidationAuditor.evaluate_jvr("")
    assert report.jvr_score == 0.0
    assert report.is_jvr_robust is False
    assert report.verdict == "SUSPECT_ORACLE"


def test_jvr_to_dict():
    diff = "+assert func() == 42\n"
    report = JointValidationAuditor.evaluate_jvr(diff)
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "jvr_score" in d
    assert "is_jvr_robust" in d
    assert "verdict" in d
    assert "reproduction_fidelity" in d
