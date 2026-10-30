"""
RepoMedic — Syntax Integrity Guard (AST & Grammar-Constrained APR 2026)

Inspired by HASTE / Copy-as-Decode (2025/2026):
Addresses the critical SWE-bench failure mode where generated patches introduce
SyntaxError or IndentationError (e.g. unclosed brackets, missing colons, invalid
indentation), wasting costly container sandbox runs and triggering full retries.

Performs static AST grammar validation in <1ms before container dispatch:
1. Parses reconstructed or modified blocks with `ast.parse()`.
2. Checks bracket/parenthesis balancing on hunk additions.
3. Intercepts syntax regressions before sandbox container allocation.
"""

from __future__ import annotations

import ast
import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class SyntaxCheckResult(NamedTuple):
    __test__ = False  # Prevent pytest collection

    is_valid: bool
    error_type: str | None      # "SyntaxError" | "IndentationError" | "BracketMismatch" | None
    error_message: str | None
    line_number: int | None
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "line_number": self.line_number,
            "details": self.details,
        }


class SyntaxIntegrityGuard:
    """Validates structural syntax and grammar integrity of candidate code patches."""

    OPENING_BRACKETS = {"(": ")", "[": "]", "{": "}"}
    CLOSING_BRACKETS = {")": "(", "]": "[", "}": "{"}

    @classmethod
    def check_bracket_balance(cls, text: str) -> tuple[bool, str | None]:
        """Verifies matching parentheses, square brackets, and curly braces."""
        stack: list[tuple[str, int]] = []
        in_string: str | None = None
        escape = False

        for i, char in enumerate(text):
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == in_string:
                    in_string = None
                continue

            if char in ("'", '"'):
                in_string = char
                continue
            elif char == "#":
                # Comment line: ignore rest of line in brackets check
                continue

            if char in cls.OPENING_BRACKETS:
                stack.append((char, i))
            elif char in cls.CLOSING_BRACKETS:
                if not stack:
                    return False, f"Unexpected closing bracket '{char}' at index {i}"
                top, _ = stack.pop()
                if cls.CLOSING_BRACKETS[char] != top:
                    return False, f"Mismatched bracket: expected closing for '{top}', got '{char}'"

        if stack:
            unclosed, idx = stack[-1]
            return False, f"Unclosed bracket '{unclosed}' originating near index {idx}"

        return True, None

    @classmethod
    def verify_code(cls, code: str, filename: str = "<patch>") -> SyntaxCheckResult:
        """Parses full code string through Python AST to detect syntax or indentation errors."""
        if not code.strip():
            return SyntaxCheckResult(
                is_valid=True,
                error_type=None,
                error_message=None,
                line_number=None,
                details="Empty code buffer verified.",
            )

        # 1. First-pass bracket balance
        is_balanced, bracket_err = cls.check_bracket_balance(code)
        if not is_balanced:
            return SyntaxCheckResult(
                is_valid=False,
                error_type="BracketMismatch",
                error_message=bracket_err,
                line_number=None,
                details=f"AST Syntax Guard intercepted syntax defect: {bracket_err}",
            )

        # 2. Complete Python AST parsing
        try:
            ast.parse(code, filename=filename)
            return SyntaxCheckResult(
                is_valid=True,
                error_type=None,
                error_message=None,
                line_number=None,
                details="AST syntax validation passed with zero parse errors.",
            )
        except IndentationError as ie:
            return SyntaxCheckResult(
                is_valid=False,
                error_type="IndentationError",
                error_message=str(ie.msg),
                line_number=ie.lineno,
                details=f"Indentation error on line {ie.lineno}: {ie.msg}",
            )
        except SyntaxError as se:
            return SyntaxCheckResult(
                is_valid=False,
                error_type="SyntaxError",
                error_message=str(se.msg),
                line_number=se.lineno,
                details=f"Syntax error on line {se.lineno}: {se.msg}",
            )
        except Exception as exc:
            return SyntaxCheckResult(
                is_valid=False,
                error_type="ParseError",
                error_message=str(exc),
                line_number=None,
                details=f"Unexpected AST parse error: {exc}",
            )

    @classmethod
    def verify_patch_hunks(cls, patch_diff: str) -> SyntaxCheckResult:
        """
        Extracts added lines from unified diff hunks and verifies internal structural syntax.
        """
        if not patch_diff or not patch_diff.strip():
            return SyntaxCheckResult(
                is_valid=True,
                error_type=None,
                error_message=None,
                line_number=None,
                details="No patch diff to check.",
            )

        # Extract only added lines
        added_lines = [
            line[1:] for line in patch_diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        hunk_code = "\n".join(added_lines)

        # Check bracket balancing across added hunk
        is_balanced, bracket_err = cls.check_bracket_balance(hunk_code)
        if not is_balanced:
            return SyntaxCheckResult(
                is_valid=False,
                error_type="BracketMismatch",
                error_message=bracket_err,
                line_number=None,
                details=f"Patch hunk contains unclosed brackets: {bracket_err}",
            )

        return SyntaxCheckResult(
            is_valid=True,
            error_type=None,
            error_message=None,
            line_number=None,
            details="Patch hunks syntax structure validated.",
        )
