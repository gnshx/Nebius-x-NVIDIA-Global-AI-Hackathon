"""
Unit tests for StaticLinterValidator (AST NameError Detection).
"""

import pytest
from services.linter_validator import StaticLinterValidator


def test_clean_python_code_passes():
    code = """
import re
from typing import Optional

def format_number(val: int, precision: Optional[int] = None) -> str:
    if precision is not None and precision < 0:
        raise ValueError("precision must be non-negative")
    return str(val)
"""
    report = StaticLinterValidator.validate_code(code)
    assert report.is_clean
    assert len(report.undefined_names) == 0
    assert not report.has_syntax_errors
    assert "passed with 0 undefined symbols" in report.details


def test_detects_undefined_variable():
    code = """
def calculate_total(price, tax_rate):
    discounted = price * discount_factor  # discount_factor is undefined!
    return discounted * (1 + tax_rate)
"""
    report = StaticLinterValidator.validate_code(code)
    assert not report.is_clean
    assert "discount_factor" in report.undefined_names
    assert report.warning_count >= 1


def test_accepts_known_globals():
    code = """
def call_external():
    return custom_global_helper(42)
"""
    # Without known globals -> fails
    report1 = StaticLinterValidator.validate_code(code)
    assert "custom_global_helper" in report1.undefined_names

    # With known globals -> passes
    report2 = StaticLinterValidator.validate_code(code, known_globals={"custom_global_helper"})
    assert report2.is_clean


def test_handles_syntax_errors():
    code = "def broken(:"
    report = StaticLinterValidator.validate_code(code)
    assert not report.is_clean
    assert report.has_syntax_errors
    assert "SyntaxError" in report.details


def test_linter_report_serialization():
    report = StaticLinterValidator.validate_code("x = 1\n")
    d = report.to_dict()
    assert "is_clean" in d
    assert "undefined_names" in d
    assert "warning_count" in d
