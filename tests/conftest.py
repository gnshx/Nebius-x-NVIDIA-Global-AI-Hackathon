"""
pytest conftest.py — Shared fixtures for all tests.
"""
from __future__ import annotations

import os
import sys

import pytest

# Add the API directory to Python path so tests can import app modules
API_DIR = os.path.join(os.path.dirname(__file__), "..", "apps", "api")
sys.path.insert(0, API_DIR)

# Set test environment before importing settings
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repomedic:repomedic@localhost:5432/repomedic_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("NEBIUS_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")
os.environ.setdefault("GITHUB_APP_ID", "12345")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default asyncio event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def sample_issue() -> dict:
    """A sample GitHub issue payload."""
    return {
        "number": 42,
        "title": "parse_user_id crashes with 'list index out of range'",
        "body": (
            "When calling `parse_user_id('user-123')` it raises "
            "`IndexError: list index out of range` instead of returning `123`.\n\n"
            "**Expected:** `parse_user_id('user-123')` returns `123`\n"
            "**Actual:** `IndexError: list index out of range`"
        ),
        "state": "open",
        "user": {"login": "reporter"},
        "html_url": "https://github.com/owner/repo/issues/42",
        "labels": [],
    }


@pytest.fixture
def sample_repository() -> dict:
    """A sample GitHub repository payload."""
    return {
        "full_name": "owner/demo-repo",
        "name": "demo-repo",
        "owner": {"login": "owner"},
        "default_branch": "main",
        "language": "Python",
        "private": False,
        "html_url": "https://github.com/owner/demo-repo",
    }


@pytest.fixture
def run_id() -> str:
    """A sample run UUID."""
    import uuid
    return str(uuid.uuid4())
