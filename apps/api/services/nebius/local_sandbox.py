"""
RepoMedic — Local Sandbox Executor

Implements the SandboxExecutor interface for local development and demos.
Supports:
1. Docker container execution (when Docker daemon is available)
2. In-process isolated temp directory subprocess execution (fallback when Docker is offline)
3. Resilient unified diff / patch application
"""

from __future__ import annotations

import asyncio
import io
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
import uuid
from pathlib import Path

import structlog

from config import settings
from .sandbox import SandboxResult, _truncate

logger = structlog.get_logger(__name__)
DOCKER_IMAGE = "python:3.12-slim"


def _apply_unified_patch_to_dir(workdir: Path, patch_text: str) -> bool:
    """Apply a unified diff patch to files in workdir using robust hunk matching."""
    # Split patch by file (--- a/ ... +++ b/ ...)
    file_patches = re.split(r"(?=^--- )", patch_text, flags=re.MULTILINE)
    applied_any = False

    for fp in file_patches:
        if not fp.strip():
            continue
        lines = fp.splitlines()
        target_file = None
        for line in lines[:5]:
            if line.startswith("+++ "):
                target_file = line[4:].strip()
                if target_file.startswith("b/"):
                    target_file = target_file[2:]
                break

        if not target_file:
            continue

        file_path = workdir / target_file
        if not file_path.exists():
            # Might be file creation
            new_lines = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++ ")]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            applied_any = True
            continue

        # Modify existing file
        orig_content = file_path.read_text(encoding="utf-8")
        orig_lines = orig_content.splitlines(keepends=True)

        # Parse hunks
        hunk_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", re.MULTILINE)
        hunk_starts = [m.start() for m in hunk_pattern.finditer(fp)]
        if not hunk_starts:
            continue

        # Extract replacements: lines with - vs +
        minus_lines = [l[1:].strip() for l in lines if l.startswith("-") and not l.startswith("--- ")]
        plus_lines = [l[1:].strip() for l in lines if l.startswith("+") and not l.startswith("+++ ")]

        if minus_lines and plus_lines:
            target_str = "\n".join(minus_lines)
            repl_str = "\n".join(plus_lines)
            # Try simple replacement if substring matches
            if target_str in orig_content:
                new_content = orig_content.replace(target_str, repl_str, 1)
                file_path.write_text(new_content, encoding="utf-8")
                applied_any = True
                continue

            # Fallback line-by-line replacement
            new_lines = []
            for oline in orig_lines:
                replaced = False
                for m_line, p_line in zip(minus_lines, plus_lines):
                    if m_line in oline:
                        new_lines.append(oline.replace(m_line, p_line))
                        replaced = True
                        break
                if not replaced:
                    new_lines.append(oline)
            file_path.write_text("".join(new_lines), encoding="utf-8")
            applied_any = True

    return applied_any


class LocalSandboxExecutor:
    """
    Local sandbox executor supporting both Docker containers and native subprocess isolation.
    """

    def __init__(self) -> None:
        self._workdirs: dict[str, Path] = {}
        self._max_log_bytes: int = settings.nebius_sandbox_max_log_bytes
        self._has_docker: bool | None = None

    def _check_docker(self) -> bool:
        if self._has_docker is None:
            self._has_docker = shutil.which("docker") is not None
        return self._has_docker

    async def create_sandbox(self, repo_tarball: bytes) -> str:
        """Extract repo tarball or seed from demo directory."""
        sandbox_id = str(uuid.uuid4())
        workdir = Path(tempfile.mkdtemp(prefix=f"repomedic-{sandbox_id[:8]}-"))
        self._workdirs[sandbox_id] = workdir

        if repo_tarball and len(repo_tarball) > 10:
            try:
                with tarfile.open(fileobj=io.BytesIO(repo_tarball), mode="r:*") as tf:
                    tf.extractall(path=workdir)
            except Exception as e:
                logger.warning("tarball_extract_failed", error=str(e))
                self._seed_demo_dir(workdir)
        else:
            self._seed_demo_dir(workdir)

        logger.info("local_sandbox_created", sandbox_id=sandbox_id, workdir=str(workdir))
        return sandbox_id

    def _seed_demo_dir(self, workdir: Path) -> None:
        """Seed workdir with demo repository files if available."""
        demo_dir = Path("demo")
        if demo_dir.exists():
            for root, _, files in os.walk(demo_dir):
                if any(ign in root for ign in [".git", "__pycache__", ".pytest_cache"]):
                    continue
                for f in files:
                    src = Path(root) / f
                    rel = src.relative_to(demo_dir)
                    dest = workdir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)

    async def apply_patch(self, sandbox_id: str, patch_content: str) -> None:
        """Apply patch to workdir files."""
        workdir = self._workdirs[sandbox_id]
        success = _apply_unified_patch_to_dir(workdir, patch_content)
        if not success:
            logger.warning("fuzzy_patch_fallback_needed", sandbox_id=sandbox_id)
        logger.info("local_patch_applied", sandbox_id=sandbox_id)

    async def install_dependencies(self, sandbox_id: str) -> SandboxResult:
        """Install dependencies."""
        return await self.execute(
            sandbox_id,
            command="pip install -e . -q",
            timeout=300,
        )

    async def execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = 300,
    ) -> SandboxResult:
        """Execute a shell command inside Docker or direct isolated subprocess."""
        workdir = self._workdirs.get(sandbox_id)
        if workdir is None:
            raise ValueError(f"Unknown sandbox_id: {sandbox_id!r}")

        logger.info("local_sandbox_exec", sandbox_id=sandbox_id, command=command)
        t0 = time.monotonic()

        use_docker = self._check_docker() and os.environ.get("USE_DOCKER_SANDBOX", "false").lower() == "true"

        if use_docker:
            cmd_args = [
                "docker", "run", "--rm",
                "-v", f"{workdir}:/workspace:z",
                "-w", "/workspace",
                DOCKER_IMAGE,
                "sh", "-c", command,
            ]
        else:
            # Native subprocess in isolated temp directory
            # If command is pytest, run with current python
            if command.startswith("pytest"):
                cmd_args = [sys.executable, "-m", "pytest"] + command.split()[1:]
            elif command.startswith("pip "):
                cmd_args = [sys.executable, "-m", "pip"] + command.split()[1:]
            else:
                cmd_args = ["bash", "-c", command]

        timed_out = False
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{workdir}:{env.get('PYTHONPATH', '')}"

            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=str(workdir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                raw_out, raw_err = await asyncio.wait_for(
                    proc.communicate(), timeout=float(timeout)
                )
                exit_code = proc.returncode or 0
                stdout = raw_out.decode("utf-8", errors="replace")
                stderr = raw_err.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                proc.kill()
                raw_out, raw_err = await proc.communicate()
                exit_code = -1
                timed_out = True
                stdout = raw_out.decode("utf-8", errors="replace")
                stderr = raw_err.decode("utf-8", errors="replace") + "\n[Execution timed out]"
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
        return SandboxResult(
            sandbox_id=sandbox_id,
            exit_code=exit_code,
            stdout=_truncate(stdout, self._max_log_bytes),
            stderr=_truncate(stderr, self._max_log_bytes),
            duration_seconds=round(duration, 2),
            timed_out=timed_out,
        )

    async def get_logs(self, sandbox_id: str) -> str:
        return ""

    async def destroy(self, sandbox_id: str) -> None:
        workdir = self._workdirs.pop(sandbox_id, None)
        if workdir and workdir.exists():
            try:
                shutil.rmtree(workdir, ignore_errors=True)
            except Exception as e:
                logger.warning("sandbox_cleanup_failed", error=str(e))
        logger.info("local_sandbox_destroyed", sandbox_id=sandbox_id)


def get_sandbox_executor() -> Any:
    """Return remote SandboxExecutor or LocalSandboxExecutor fallback."""
    if settings.nebius_sandbox_url and "placeholder" not in str(settings.nebius_sandbox_url).lower():
        from .sandbox import SandboxExecutor
        return SandboxExecutor()
    return LocalSandboxExecutor()
