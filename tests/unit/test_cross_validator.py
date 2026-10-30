"""Unit tests for RepoMedic's PatchCrossValidator (TEX)."""

import pytest
from services.cross_validator import PatchCrossValidator, CrossValidationReport


def test_clean_patch_passes_cross_validation():
    files = [
        {
            "path": "src/module.py",
            "diff": "@@ -10,3 +10,5 @@\n+    if x < 0:\n+        raise ValueError('x must be >= 0')",
        },
        {
            "path": "tests/test_module.py",
            "diff": "@@ -20,3 +20,6 @@\n+def test_negative_x():\n+    with pytest.raises(ValueError):\n+        func(-1)",
        },
    ]

    report = PatchCrossValidator.validate_patch(files)
    assert report.is_safe is True
    assert report.invariant_score == 1.0
    assert len(report.violations) == 0
    assert len(report.warnings) == 0
    assert report.modified_source_count == 1
    assert report.modified_test_count == 1


def test_cross_validator_detects_skipped_test():
    files = [
        {
            "path": "tests/test_calc.py",
            "diff": "@@ -5,3 +5,4 @@\n+@pytest.mark.skip(reason='temp fix')\n def test_failing():",
        }
    ]

    report = PatchCrossValidator.validate_patch(files)
    assert report.is_safe is False
    assert report.invariant_score <= 0.70
    assert any("Injected @pytest.mark.skip" in v for v in report.violations)


def test_cross_validator_detects_commented_out_assertion():
    files = [
        {
            "path": "tests/test_calc.py",
            "diff": "@@ -15,3 +15,4 @@\n+#   assert result == expected\n",
        }
    ]

    report = PatchCrossValidator.validate_patch(files)
    assert report.is_safe is False
    assert any("Commented out test assertion" in v for v in report.violations)


def test_cross_validator_warns_on_function_deletion():
    files = [
        {
            "path": "src/api.py",
            "diff": "@@ -30,6 +30,1 @@\n-def legacy_endpoint():\n-    pass",
        }
    ]

    report = PatchCrossValidator.validate_patch(files)
    assert report.is_safe is True  # Warning, not hard violation
    assert report.invariant_score < 1.0
    assert any("Deleted function definition" in w for w in report.warnings)


def test_cross_validator_to_dict():
    files = [{"path": "src/foo.py", "diff": "+x = 1"}]
    report = PatchCrossValidator.validate_patch(files)
    d = report.to_dict()

    assert isinstance(d, dict)
    assert "is_safe" in d
    assert "invariant_score" in d
    assert "violations" in d
