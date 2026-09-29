"""
Integration test: GitHub webhook signature verification.

Tests that:
- Valid signatures are accepted
- Invalid signatures are rejected
- Missing signature header is rejected
"""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
def webhook_secret() -> str:
    return "test-webhook-secret-12345"


@pytest.fixture
def sample_issue_comment_payload() -> dict:
    return {
        "action": "created",
        "comment": {"body": "/repomedic fix", "id": 1},
        "issue": {"number": 42, "title": "parse_user_id crashes"},
        "repository": {"full_name": "owner/repo", "id": 123},
        "installation": {"id": 456},
    }


def make_signature(secret: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


class TestWebhookSignatureVerification:
    """Tests for GitHub webhook HMAC verification."""

    @pytest.mark.asyncio
    async def test_valid_signature_accepted(
        self, sample_issue_comment_payload, webhook_secret, monkeypatch
    ):
        """A request with correct HMAC signature should be processed."""
        import config
        monkeypatch.setattr(
            config.settings,
            "github_webhook_secret",
            type("S", (), {"get_secret_value": lambda self: webhook_secret})(),
        )

        body = json.dumps(sample_issue_comment_payload).encode()
        sig = make_signature(webhook_secret, body)

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the webhook dispatch to avoid side effects
            import services.github.webhook as wh
            original = wh.dispatch_webhook
            wh.dispatch_webhook = lambda e, p: {"status": "ok"}  # type: ignore

            try:
                resp = await client.post(
                    "/api/github/webhook",
                    content=body,
                    headers={
                        "X-GitHub-Event": "issue_comment",
                        "X-Hub-Signature-256": sig,
                        "X-GitHub-Delivery": "test-delivery-id",
                        "Content-Type": "application/json",
                    },
                )
                assert resp.status_code == 200
            finally:
                wh.dispatch_webhook = original

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(
        self, sample_issue_comment_payload, webhook_secret, monkeypatch
    ):
        """A request with wrong HMAC signature must return 401."""
        import config
        monkeypatch.setattr(
            config.settings,
            "github_webhook_secret",
            type("S", (), {"get_secret_value": lambda self: webhook_secret})(),
        )

        body = json.dumps(sample_issue_comment_payload).encode()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/github/webhook",
                content=body,
                headers={
                    "X-GitHub-Event": "issue_comment",
                    "X-Hub-Signature-256": "sha256=wrongsignaturevalue",
                    "X-GitHub-Delivery": "test-delivery-id",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_signature_rejected(
        self, sample_issue_comment_payload, webhook_secret, monkeypatch
    ):
        """A request without X-Hub-Signature-256 must return 401."""
        import config
        monkeypatch.setattr(
            config.settings,
            "github_webhook_secret",
            type("S", (), {"get_secret_value": lambda self: webhook_secret})(),
        )

        body = json.dumps(sample_issue_comment_payload).encode()

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/github/webhook",
                content=body,
                headers={
                    "X-GitHub-Event": "issue_comment",
                    "Content-Type": "application/json",
                },
            )
            # 401 or 422 (missing required header)
            assert resp.status_code in (401, 422)
