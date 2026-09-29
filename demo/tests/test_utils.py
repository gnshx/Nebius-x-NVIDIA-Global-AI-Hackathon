"""
demo_repo/tests/test_utils.py

Tests for the utility functions.
The test_parse_user_id test will FAIL due to the bug in parse_user_id.
RepoMedic should find and fix this.
"""
from __future__ import annotations

import pytest

from src.utils import (
    format_user_id,
    normalize_email,
    parse_user_id,
    validate_username,
)


class TestParseUserId:
    """Tests for parse_user_id — these will FAIL with the current bug."""

    def test_basic_parse(self):
        """Standard user-{id} format should return the integer ID."""
        assert parse_user_id("user-123") == 123

    def test_single_digit(self):
        assert parse_user_id("user-1") == 1

    def test_large_id(self):
        assert parse_user_id("user-99999") == 99999

    def test_invalid_format_raises(self):
        """Non-standard format should raise an appropriate error."""
        with pytest.raises((ValueError, IndexError)):
            parse_user_id("notauser")

    def test_roundtrip(self):
        """parse_user_id(format_user_id(n)) should return n."""
        for n in [1, 42, 1000, 99999]:
            assert parse_user_id(format_user_id(n)) == n


class TestFormatUserId:
    """Tests for format_user_id — these should PASS."""

    def test_basic(self):
        assert format_user_id(123) == "user-123"

    def test_zero(self):
        assert format_user_id(0) == "user-0"

    def test_large(self):
        assert format_user_id(99999) == "user-99999"


class TestValidateUsername:
    """Tests for validate_username — these should PASS."""

    def test_valid(self):
        assert validate_username("alice") is True
        assert validate_username("bob_99") is True
        assert validate_username("Alice123") is True

    def test_too_short(self):
        assert validate_username("ab") is False

    def test_too_long(self):
        assert validate_username("a" * 31) is False

    def test_starts_with_digit(self):
        assert validate_username("1alice") is False

    def test_special_chars(self):
        assert validate_username("alice!") is False


class TestNormalizeEmail:
    """Tests for normalize_email — these should PASS."""

    def test_lowercases(self):
        assert normalize_email("ALICE@EXAMPLE.COM") == "alice@example.com"

    def test_strips_whitespace(self):
        assert normalize_email("  alice@example.com  ") == "alice@example.com"

    def test_no_change_needed(self):
        assert normalize_email("alice@example.com") == "alice@example.com"
