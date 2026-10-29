"""
Unit tests for TestImpactAnalyzer and enhanced PatchValidator.
"""

import pytest
from services.test_selector import TestImpactAnalyzer
from agents.nodes.implementation import PatchValidator
from models.schemas import Patch, FileChange


def test_test_impact_analyzer_exact_match():
    modified = ["src/humanize/number.py"]
    available = [
        "tests/test_number.py",
        "tests/test_time.py",
        "tests/test_filesize.py",
    ]
    impacted = TestImpactAnalyzer.select_impacted_tests(modified, available)
    assert impacted == ["tests/test_number.py"]


def test_test_impact_analyzer_submodule_match():
    modified = ["auth/tokens.py"]
    available = [
        "tests/test_tokens_refresh.py",
        "tests/test_users.py",
    ]
    impacted = TestImpactAnalyzer.select_impacted_tests(modified, available)
    assert impacted == ["tests/test_tokens_refresh.py"]


def test_test_impact_analyzer_fallback():
    modified = ["misc/weird_helper.py"]
    available = [
        "tests/test_number.py",
        "tests/test_time.py",
    ]
    impacted = TestImpactAnalyzer.select_impacted_tests(modified, available)
    # Falls back to running all tests to guarantee zero missed regressions
    assert impacted == available


def test_test_impact_analyzer_build_command():
    cmd = TestImpactAnalyzer.build_test_command(["tests/test_number.py"], verbose=True)
    assert cmd == "pytest -v --tb=short tests/test_number.py"


def test_patch_validator_blocks_traversal():
    validator = PatchValidator()
    
    # Check .. in path
    bad_patch = Patch(
        summary="Test traversal",
        files=[FileChange(path="src/../../etc/passwd", operation="modify", patch="+hacked", reason="test")]
    )
    with pytest.raises(ValueError, match="Directory traversal rejected|Blocked path pattern"):
        validator.validate(bad_patch)


def test_patch_validator_blocks_credentials():
    validator = PatchValidator()
    
    bad_patch = Patch(
        summary="Test cert",
        files=[FileChange(path="certs/server.pem", operation="modify", patch="+cert", reason="test")]
    )
    with pytest.raises(ValueError, match="Blocked file extension"):
        validator.validate(bad_patch)

    bad_patch2 = Patch(
        summary="Test env",
        files=[FileChange(path="config/.env", operation="modify", patch="+secret", reason="test")]
    )
    with pytest.raises(ValueError, match="Blocked file extension|Blocked path pattern"):
        validator.validate(bad_patch2)


def test_patch_validator_accepts_clean_patch():
    validator = PatchValidator()
    
    clean_patch = Patch(
        summary="Test clean patch",
        files=[
            FileChange(
                path="src/humanize/number.py",
                operation="modify",
                patch="--- a/src/humanize/number.py\n+++ b/src/humanize/number.py\n+    if ndigits < 0:\n+        raise ValueError()",
                reason="Input validation"
            )
        ]
    )
    # Should not raise
    validator.validate(clean_patch)
