"""
Unit tests for patch validation (security).

Tests path traversal rejection, blocked extensions,
absolute paths, and .git manipulation prevention.
"""
from __future__ import annotations

import pytest

from agents.nodes.implementation import PatchValidator
from models.schemas import FileChange, Patch


def make_patch(path: str, operation: str = "modify") -> Patch:
    """Helper to create a Patch with a single file change."""
    return Patch(
        files=[FileChange(path=path, operation=operation, patch="--- a\n+++ b\n", reason="test")],
        summary="test patch",
    )


@pytest.fixture
def validator():
    return PatchValidator()


class TestPathTraversalRejection:
    """Path traversal attacks must be rejected."""

    def test_rejects_dotdot(self, validator):
        with pytest.raises(ValueError, match="Blocked path"):
            validator.validate(make_patch("../etc/passwd"))

    def test_rejects_dotdot_nested(self, validator):
        with pytest.raises(ValueError, match="Blocked path"):
            validator.validate(make_patch("src/../../secret"))

    def test_rejects_absolute_path(self, validator):
        with pytest.raises(ValueError, match="Absolute path"):
            validator.validate(make_patch("/etc/passwd"))

    def test_rejects_absolute_path_root(self, validator):
        with pytest.raises(ValueError, match="Absolute path"):
            validator.validate(make_patch("/home/user/.ssh/id_rsa"))


class TestBlockedExtensions:
    """Credential and key files must be rejected."""

    def test_rejects_pem(self, validator):
        with pytest.raises(ValueError, match="Blocked file extension"):
            validator.validate(make_patch("certs/server.pem"))

    def test_rejects_key(self, validator):
        with pytest.raises(ValueError, match="Blocked file extension"):
            validator.validate(make_patch("keys/private.key"))

    def test_rejects_env(self, validator):
        with pytest.raises(ValueError, match="Blocked file extension"):
            validator.validate(make_patch(".env"))

    def test_rejects_p12(self, validator):
        with pytest.raises(ValueError, match="Blocked file extension"):
            validator.validate(make_patch("certs/client.p12"))


class TestBlockedPaths:
    """Git directory and other system paths must be rejected."""

    def test_rejects_git_dir(self, validator):
        with pytest.raises(ValueError, match="Blocked path"):
            validator.validate(make_patch(".git/config"))

    def test_rejects_git_hooks(self, validator):
        with pytest.raises(ValueError, match="Blocked path"):
            validator.validate(make_patch(".git/hooks/pre-commit"))


class TestValidPaths:
    """Legitimate source file paths should pass validation."""

    def test_accepts_python_file(self, validator):
        validator.validate(make_patch("src/utils.py"))  # should not raise

    def test_accepts_test_file(self, validator):
        validator.validate(make_patch("tests/test_utils.py"))

    def test_accepts_nested_path(self, validator):
        validator.validate(make_patch("src/services/github/client.py"))

    def test_accepts_new_file(self, validator):
        validator.validate(make_patch("src/new_module.py", operation="create"))

    def test_accepts_config_file(self, validator):
        validator.validate(make_patch("pyproject.toml"))
