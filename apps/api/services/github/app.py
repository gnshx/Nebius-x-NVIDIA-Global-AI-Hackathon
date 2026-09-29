"""
RepoMedic — GitHub App Authentication
Handles installation tokens, webhook signature verification.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import httpx
import jwt

from config import settings


class GitHubApp:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self._installation_tokens: dict[int, tuple[str, datetime]] = {}

    def _generate_jwt(self) -> str:
        """Generate a GitHub App JWT (valid 10 minutes)."""
        now = int(time.time())
        payload = {
            "iat": now - 60,  # issued 60s ago to allow clock skew
            "exp": now + (10 * 60),
            "iss": settings.github_app_id,
        }
        return jwt.encode(payload, settings.github_private_key_resolved, algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> str:
        """Get a cached installation access token, refreshing if needed."""
        cached = self._installation_tokens.get(installation_id)
        if cached:
            token, expires_at = cached
            if datetime.now(timezone.utc) < expires_at - timedelta(minutes=5):
                return token

        # Fetch new token
        jwt_token = self._generate_jwt()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        self._installation_tokens[installation_id] = (token, expires_at)
        return token

    def verify_webhook_signature(self, payload: bytes, signature_header: str) -> bool:
        """Verify the X-Hub-Signature-256 header."""
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        secret = settings.github_webhook_secret.get_secret_value().encode()
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        received = signature_header[len("sha256="):]
        return hmac.compare_digest(expected, received)


github_app = GitHubApp()
