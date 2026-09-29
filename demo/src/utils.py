"""
demo_repo/src/utils.py

This module contains intentionally buggy utility functions
for the RepoMedic demonstration.
"""
from __future__ import annotations


def parse_user_id(value: str) -> int:
    """
    Parse a user ID from a formatted string.

    Expected format: 'user-{id}' (e.g., 'user-123')

    Returns:
        The integer user ID.

    Raises:
        ValueError: If the format is invalid.
        IndexError: If splitting produces unexpected results.
    """
    # BUG: Uses split(" ") instead of split("-")
    # This causes an IndexError for all valid inputs like "user-123"
    parts = value.split(" ")
    return int(parts[1])


def format_user_id(user_id: int) -> str:
    """Format an integer user ID into the standard string format."""
    return f"user-{user_id}"


def validate_username(username: str) -> bool:
    """
    Validate that a username meets requirements:
    - 3–30 characters
    - Alphanumeric and underscores only
    - Must start with a letter
    """
    if not (3 <= len(username) <= 30):
        return False
    if not username[0].isalpha():
        return False
    return all(c.isalnum() or c == "_" for c in username)


def normalize_email(email: str) -> str:
    """Normalize an email address to lowercase and strip whitespace."""
    return email.strip().lower()
