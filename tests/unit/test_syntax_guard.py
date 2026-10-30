"""
Unit tests for SyntaxIntegrityGuard (AST & Grammar-Constrained APR).
"""

import pytest
from services.syntax_guard import SyntaxIntegrityGuard


def test_verify_valid_python_code():
    code = """
def intcomma(value, ndigits=None):
    if ndigits is not None and ndigits < 0:
        raise ValueError("ndigits must be non-negative")
    return str(value)
"""
    result = SyntaxIntegrityGuard.verify_code(code)
    assert result.is_valid
    assert result.error_type is None
    assert "validation passed" in result.details


def test_verify_bracket_mismatch():
    code = "def bad_func():\n    data = {'key': [1, 2, 3)\n"
    result = SyntaxIntegrityGuard.verify_code(code)
    assert not result.is_valid
    assert result.error_type == "BracketMismatch"
    assert "Mismatched bracket" in result.details or "Unclosed" in result.details


def test_verify_unclosed_parenthesis():
    code = "def bad_func():\n    call_something(123, 456\n"
    result = SyntaxIntegrityGuard.verify_code(code)
    assert not result.is_valid
    assert result.error_type == "BracketMismatch"
    assert "Unclosed bracket" in result.details


def test_verify_indentation_error():
    code = "def bad_indent():\nif True:\n    pass\n"
    result = SyntaxIntegrityGuard.verify_code(code)
    assert not result.is_valid
    assert result.error_type == "IndentationError"
    assert result.line_number is not None


def test_verify_syntax_error():
    code = "def broken_syntax():\n    x = = 12\n"
    result = SyntaxIntegrityGuard.verify_code(code)
    assert not result.is_valid
    assert result.error_type == "SyntaxError"
    assert result.line_number is not None


def test_verify_patch_hunks_clean():
    diff = """
--- a/src/utils.py
+++ b/src/utils.py
@@ -10,3 +10,6 @@
+    if value is None:
+        return ""
"""
    result = SyntaxIntegrityGuard.verify_patch_hunks(diff)
    assert result.is_valid


def test_verify_patch_hunks_unclosed_bracket():
    diff = """
--- a/src/utils.py
+++ b/src/utils.py
@@ -10,3 +10,6 @@
+    parts = value.split(" "
"""
    result = SyntaxIntegrityGuard.verify_patch_hunks(diff)
    assert not result.is_valid
    assert result.error_type == "BracketMismatch"


def test_syntax_guard_serialization():
    result = SyntaxIntegrityGuard.verify_code("x = 42\n")
    d = result.to_dict()
    assert "is_valid" in d
    assert d["is_valid"] is True
    assert "details" in d
