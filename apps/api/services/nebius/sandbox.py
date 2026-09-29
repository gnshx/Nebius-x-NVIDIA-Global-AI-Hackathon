"""
RepoMedic — Nebius Sandbox Executor

Provides a remote code-execution sandbox via the Nebius Sandbox API.
All interactions are async; stdout/stderr are truncated to a safe byte limit.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from pydantic import BaseModel

from config import settings

logger = structlog.get_logger(__name__)


class SandboxResult(BaseModel):
    sandbox_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


def _truncate(text: str, max_bytes: int) -> str:
    """Truncate a string to at most `max_bytes` UTF-8 bytes."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + f"\n... [truncated to {max_bytes} bytes]"


class SandboxExecutor:
    """Async client for the Nebius Sandbox REST API."""

    def __init__(self) -> None:
        self._base_url = str(settings.nebius_sandbox_url).rstrip("/")
        self._max_log_bytes: int = settings.nebius_sandbox_max_log_bytes

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {settings.nebius_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            },
            timeout=360,
        )

    async def create_sandbox(self, repo_tarball: bytes) -> str:
        """
        Upload a repo tarball and create a new sandbox.
        Returns the sandbox_id assigned by the service.
        """
        async with self._client() as client:
            resp = await client.post(
                "/sandboxes",
                content=repo_tarball,
                headers={"Content-Type": "application/octet-stream"},
            )
        resp.raise_for_status()
        sandbox_id: str = resp.json()["sandbox_id"]
        logger.info("sandbox_created", sandbox_id=sandbox_id)
        return sandbox_id

    async def apply_patch(self, sandbox_id: str, patch_content: str) -> None:
        """Apply a unified-diff patch inside an existing sandbox."""
        async with self._client() as client:
            resp = await client.post(
                f"/sandboxes/{sandbox_id}/patch",
                json={"patch": patch_content},
            )
        resp.raise_for_status()
        logger.info("patch_applied", sandbox_id=sandbox_id)

    async def install_dependencies(self, sandbox_id: str) -> SandboxResult:
        """Run dependency installation inside the sandbox."""
        return await self.execute(
            sandbox_id,
            command="pip install -r requirements.txt",
            timeout=300,
        )

    async def execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = 300,
    ) -> SandboxResult:
        """
        Execute an arbitrary shell command inside the sandbox.
        Waits for completion and returns stdout/stderr/exit_code.
        """
        logger.info("sandbox_execute", sandbox_id=sandbox_id, command=command)
        t0 = time.monotonic()

        async with self._client() as client:
            resp = await client.post(
                f"/sandboxes/{sandbox_id}/exec",
                json={"command": command, "timeout": timeout},
            )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        duration = time.monotonic() - t0
        stdout = _truncate(data.get("stdout", ""), self._max_log_bytes)
        stderr = _truncate(data.get("stderr", ""), self._max_log_bytes)
        timed_out: bool = data.get("timed_out", False)
        exit_code: int = data.get("exit_code", -1)

        logger.info(
            "sandbox_exec_done",
            sandbox_id=sandbox_id,
            exit_code=exit_code,
            duration=round(duration, 2),
            timed_out=timed_out,
        )
        return SandboxResult(
            sandbox_id=sandbox_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=round(duration, 2),
            timed_out=timed_out,
        )

    async def get_logs(self, sandbox_id: str) -> str:
        """Retrieve aggregated logs from a sandbox."""
        async with self._client() as client:
            resp = await client.get(f"/sandboxes/{sandbox_id}/logs")
        resp.raise_for_status()
        raw = resp.json().get("logs", "")
        return _truncate(raw, self._max_log_bytes)

    async def destroy(self, sandbox_id: str) -> None:
        """Destroy a sandbox and free its resources."""
        async with self._client() as client:
            resp = await client.delete(f"/sandboxes/{sandbox_id}")
        resp.raise_for_status()
        logger.info("sandbox_destroyed", sandbox_id=sandbox_id)
