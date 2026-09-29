"""
RepoMedic — Local (Docker-backed) Sandbox Executor

Implements the same interface as SandboxExecutor but runs commands inside
a disposable Docker container.  Intended for local development only.

NEVER deploy this executor in production.
"""
from __future__ import annotations

import asyncio
import io
import tarfile
import tempfile
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from config import settings
from .sandbox import SandboxResult, _truncate

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

DOCKER_IMAGE = "python:3.12-slim"


class LocalSandboxExecutor:
    """
    Development-only sandbox that mounts repo content into a Docker container
    and executes commands via `asyncio.create_subprocess_exec`.
    """

    def __init__(self) -> None:
        assert settings.is_development, "LocalSandboxExecutor is only for development"
        self._workdirs: dict[str, Path] = {}
        self._max_log_bytes: int = settings.nebius_sandbox_max_log_bytes

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    async def create_sandbox(self, repo_tarball: bytes) -> str:
        """
        Extract the repo tarball into a temp directory and return a sandbox_id.
        The directory is reused for subsequent exec/patch calls.
        """
        sandbox_id = str(uuid.uuid4())
        workdir = Path(tempfile.mkdtemp(prefix=f"repomedic-{sandbox_id[:8]}-"))
        self._workdirs[sandbox_id] = workdir

        # Extract tarball
        with tarfile.open(fileobj=io.BytesIO(repo_tarball), mode="r:*") as tf:
            tf.extractall(path=workdir)

        logger.info("local_sandbox_created", sandbox_id=sandbox_id, workdir=str(workdir))
        return sandbox_id

    async def apply_patch(self, sandbox_id: str, patch_content: str) -> None:
        """Write the patch to a temp file and apply it with `patch -p1`."""
        workdir = self._workdirs[sandbox_id]
        patch_file = workdir / "_repomedic.patch"
        patch_file.write_text(patch_content, encoding="utf-8")

        result = await self.execute(sandbox_id, f"patch -p1 < {patch_file}", timeout=60)
        if result.exit_code != 0:
            raise RuntimeError(
                f"patch failed (exit {result.exit_code}):\n{result.stderr}"
            )
        logger.info("local_patch_applied", sandbox_id=sandbox_id)

    async def install_dependencies(self, sandbox_id: str) -> SandboxResult:
        """Install Python dependencies from requirements.txt."""
        return await self.execute(
            sandbox_id,
            command="pip install -r requirements.txt --quiet",
            timeout=300,
        )

    # ------------------------------------------------------------------ #
    #  Execution                                                           #
    # ------------------------------------------------------------------ #

    async def execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = 300,
    ) -> SandboxResult:
        """
        Run `command` inside a fresh Docker container mounted at workdir.
        Uses `asyncio.create_subprocess_exec` for non-blocking execution.
        """
        workdir = self._workdirs.get(sandbox_id)
        if workdir is None:
            raise ValueError(f"Unknown sandbox_id: {sandbox_id!r}")

        logger.info("local_sandbox_exec", sandbox_id=sandbox_id, command=command)
        t0 = time.monotonic()

        docker_args = [
            "docker", "run", "--rm",
            "--network=none",  # no outbound network
            "-v", f"{workdir}:/workspace:z",
            "-w", "/workspace",
            DOCKER_IMAGE,
            "sh", "-c", command,
        ]

        timed_out = False
        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                raw_out, raw_err = await asyncio.wait_for(
                    proc.communicate(), timeout=float(timeout)
                )
                exit_code = proc.returncode or 0
            except asyncio.TimeoutError:
                proc.kill()
                raw_out, raw_err = await proc.communicate()
                exit_code = -1
                timed_out = True
        except Exception as exc:
            duration = time.monotonic() - t0
            logger.error("local_sandbox_exec_failed", sandbox_id=sandbox_id, error=str(exc))
            return SandboxResult(
                sandbox_id=sandbox_id,
                exit_code=-1,
                stdout="",
                stderr=str(exc),
                duration_seconds=round(duration, 2),
                timed_out=False,
            )

        duration = time.monotonic() - t0
        stdout = _truncate(raw_out.decode("utf-8", errors="replace"), self._max_log_bytes)
        stderr = _truncate(raw_err.decode("utf-8", errors="replace"), self._max_log_bytes)

        logger.info(
            "local_sandbox_exec_done",
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
        """Return a note; Docker containers are ephemeral so logs aren't retained."""
        return f"[LocalSandboxExecutor] No persistent logs for sandbox {sandbox_id!r}."

    async def destroy(self, sandbox_id: str) -> None:
        """Remove the temporary workdir for the sandbox."""
        import shutil

        workdir = self._workdirs.pop(sandbox_id, None)
        if workdir and workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)
        logger.info("local_sandbox_destroyed", sandbox_id=sandbox_id)


# ------------------------------------------------------------------ #
#  Factory                                                             #
# ------------------------------------------------------------------ #

def get_sandbox_executor() -> "SandboxExecutor | LocalSandboxExecutor":
    """
    Return the appropriate sandbox executor based on settings.

    Priority:
    1. Remote SandboxExecutor if nebius_sandbox_url is configured.
    2. LocalSandboxExecutor if running in development mode.
    3. RuntimeError otherwise.
    """
    from .sandbox import SandboxExecutor

    if settings.nebius_sandbox_url:
        return SandboxExecutor()
    if settings.is_development:
        return LocalSandboxExecutor()
    raise RuntimeError(
        "No sandbox executor available: set NEBIUS_SANDBOX_URL or IS_DEVELOPMENT=true."
    )
