"""
RepoMedic — Node: SANDBOX_EXECUTION

Executes the current patch in an isolated sandbox and collects test results.

Steps:
1. Obtain the sandbox executor (remote or local-Docker).
2. Upload the repo snapshot tarball and create a sandbox.
3. Apply the combined patch.
4. Install the package in editable mode.
5. Run the test command from the plan.
6. Parse results via TestResultParser.
7. Persist SandboxRun + TestResult records to the database.
8. Always destroy the sandbox in a finally block.

Increments `iteration` in state.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import structlog

from agents.nodes.base import node_context
from agents.state import RepoMedicState
from db.database import AsyncSessionLocal
from models.orm import AgentRun, SandboxRun, StepType, TestResult
from services.nebius.local_sandbox import get_sandbox_executor

logger = structlog.get_logger(__name__)


class TestResultParser:
    """
    Parse pytest output (plain text or --json-report) into a structured dict.

    Handles both the json-report plugin output (if present) and falls back to
    regex-based parsing of pytest's standard text output.
    """

    _SUMMARY_RE = re.compile(
        r"(?P<failed>\d+) failed|(?P<passed>\d+) passed|(?P<error>\d+) error",
        re.IGNORECASE,
    )
    _FAIL_HDR_RE = re.compile(r"^FAILED (.+?) -", re.MULTILINE)

    def parse(self, stdout: str, stderr: str, exit_code: int) -> dict:
        """Return a dict compatible with the TestResultSchema."""
        success = exit_code == 0

        # Counts from summary line
        tests_total = tests_passed = tests_failed = tests_skipped = None
        for m in self._SUMMARY_RE.finditer(stdout):
            if m.group("passed"):
                tests_passed = int(m.group("passed"))
            if m.group("failed"):
                tests_failed = int(m.group("failed"))

        if tests_passed is not None or tests_failed is not None:
            tests_total = (tests_passed or 0) + (tests_failed or 0)

        # Failing test names
        failing_test_names = self._FAIL_HDR_RE.findall(stdout)
        failing_tests = [
            {
                "name": name.strip(),
                "error_type": "AssertionError",
                "message": "",
                "traceback": "",
            }
            for name in failing_test_names
        ]

        # Failure summary: last 30 lines of output
        tail = "\n".join((stdout + "\n" + stderr).splitlines()[-30:])

        return {
            "success": success,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": 0.0,
            "tests_total": tests_total,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_skipped": tests_skipped,
            "failure_summary": tail if not success else None,
            "failing_tests": failing_tests,
        }


_parser = TestResultParser()


def _build_combined_patch(current_patch: dict) -> str:
    """Concatenate all file-level unified diffs into one patch string."""
    parts: list[str] = []
    for fc in current_patch.get("files", []):
        patch_text = fc.get("patch", "").strip()
        if patch_text:
            parts.append(patch_text)
    return "\n\n".join(parts)


async def run(state: RepoMedicState) -> dict:
    """Apply the patch in a sandbox, run tests, persist results."""
    current_patch = state.get("current_patch") or {}
    plan = state.get("plan") or {}
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)
    repo_snapshot_path: str | None = state.get("repo_snapshot_path")

    test_command: str = plan.get("test_command") or "pytest --tb=short --json-report"

    logger.info(
        "sandbox_execution_start",
        run_id=run_id,
        iteration=iteration,
        test_command=test_command,
    )

    async with node_context(
        run_id,
        StepType.SANDBOX_EXECUTION,
        iteration,
        None,
        {"iteration": iteration, "test_command": test_command},
    ):
        executor = get_sandbox_executor()
        sandbox_id: str | None = None

        # Load repo tarball
        if repo_snapshot_path and Path(repo_snapshot_path).exists():
            tarball = Path(repo_snapshot_path).read_bytes()
        else:
            logger.warning(
                "sandbox_no_snapshot",
                run_id=run_id,
                path=repo_snapshot_path,
            )
            tarball = b""  # executor will handle gracefully or raise

        combined_patch = _build_combined_patch(current_patch)

        try:
            # 1. Create sandbox
            sandbox_id = await executor.create_sandbox(tarball)
            logger.info("sandbox_created", run_id=run_id, sandbox_id=sandbox_id)

            # 2. Apply patch
            if combined_patch.strip():
                await executor.apply_patch(sandbox_id, combined_patch)
                logger.info("sandbox_patch_applied", sandbox_id=sandbox_id)

            # 3. Install dependencies
            install_result = await executor.execute(
                sandbox_id, "pip install -e . -q", timeout=300
            )
            logger.info(
                "sandbox_install_done",
                sandbox_id=sandbox_id,
                exit_code=install_result.exit_code,
            )

            # 4. Run tests
            test_result_raw = await executor.execute(
                sandbox_id, test_command, timeout=300
            )

        finally:
            if sandbox_id:
                try:
                    await executor.destroy(sandbox_id)
                    logger.info("sandbox_destroyed", sandbox_id=sandbox_id)
                except Exception as destroy_exc:
                    logger.warning(
                        "sandbox_destroy_failed",
                        sandbox_id=sandbox_id,
                        error=str(destroy_exc),
                    )

    # 5. Parse test results
    test_result = _parser.parse(
        stdout=test_result_raw.stdout,
        stderr=test_result_raw.stderr,
        exit_code=test_result_raw.exit_code,
    )
    test_result["duration_seconds"] = test_result_raw.duration_seconds

    # 6. Persist SandboxRun + TestResult to DB
    sandbox_run_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        sandbox_run = SandboxRun(
            id=uuid.UUID(sandbox_run_id),
            agent_run_id=uuid.UUID(run_id),
            sandbox_id=sandbox_id,
            iteration=iteration,
            exit_code=test_result_raw.exit_code,
            stdout=test_result_raw.stdout,
            stderr=test_result_raw.stderr,
            duration_seconds=test_result_raw.duration_seconds,
            timed_out=test_result_raw.timed_out,
            command=test_command,
        )
        session.add(sandbox_run)
        await session.flush()

        db_test_result = TestResult(
            sandbox_run_id=uuid.UUID(sandbox_run_id),
            success=test_result["success"],
            tests_total=test_result.get("tests_total"),
            tests_passed=test_result.get("tests_passed"),
            tests_failed=test_result.get("tests_failed"),
            tests_skipped=test_result.get("tests_skipped"),
            failure_summary=test_result.get("failure_summary"),
            failing_tests=test_result.get("failing_tests", []),
            raw_output=(test_result_raw.stdout + "\n" + test_result_raw.stderr)[:50_000],
        )
        session.add(db_test_result)

        # Update agent_run iteration counter
        agent_run = await session.get(AgentRun, uuid.UUID(run_id))
        if agent_run:
            agent_run.iteration = iteration + 1

        await session.commit()

    logger.info(
        "sandbox_execution_complete",
        run_id=run_id,
        sandbox_run_id=sandbox_run_id,
        success=test_result["success"],
        exit_code=test_result["exit_code"],
    )

    return {
        "test_result": test_result,
        "sandbox_run_id": sandbox_run_id,
        "iteration": iteration + 1,
    }
