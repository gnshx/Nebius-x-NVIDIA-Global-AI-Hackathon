"""
RepoMedic — pytest Output Parser

Parses raw test output into structured TestResult.
Supports: --json-report JSON output (preferred), plain text fallback.
"""

from __future__ import annotations

import json
import re
from typing import Any

import structlog

from models.schemas import FailingTestSchema, TestResultSchema

logger = structlog.get_logger(__name__)

# Regex patterns for plain text pytest output
_SUMMARY_PATTERN = re.compile(
    r"=+ (?:(\d+) passed)?(?:,? ?(\d+) failed)?(?:,? ?(\d+) error(?:ed)?)?(?:,? ?(\d+) skipped)? in ([\d.]+)s"
)
_FAILED_LINE = re.compile(r"^FAILED (.+?)(?:\s+-\s+(.+))?$", re.MULTILINE)
_ERROR_TYPE = re.compile(r"([\w.]+Error|[\w.]+Exception|AssertionError)")


class TestResultParser:
    """Parse pytest output into structured TestResult."""

    def parse(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResultSchema:
        """
        Parse test output. Tries JSON first, falls back to text parsing.
        """
        # Attempt JSON report parse (pytest --json-report)
        result = self._try_json_parse(exit_code, stdout, stderr, duration_seconds)
        if result is not None:
            return result

        # Fall back to text parsing
        return self._text_parse(exit_code, stdout, stderr, duration_seconds)

    def _try_json_parse(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResultSchema | None:
        """Try to find and parse --json-report JSON in stdout."""
        # json-report writes to .report.json by default; some setups print it
        # Also support inline JSON blocks
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("{") and "\"summary\"" in stripped:
                try:
                    data = json.loads(stripped)
                    return self._from_json_report(data, exit_code, stdout, stderr, duration_seconds)
                except (json.JSONDecodeError, KeyError):
                    continue
        return None

    def _from_json_report(
        self,
        data: dict[str, Any],
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResultSchema:
        summary = data.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        error = summary.get("error", 0)
        skipped = summary.get("skipped", 0)
        total = summary.get("total", passed + failed + error + skipped)

        failing = failed + error
        failing_tests = []
        for test in data.get("tests", []):
            if test.get("outcome") in ("failed", "error"):
                call = test.get("call", {})
                longrepr = call.get("longrepr", "")
                error_type = self._extract_error_type(longrepr)
                failing_tests.append(
                    FailingTestSchema(
                        name=test.get("nodeid", "unknown"),
                        error_type=error_type,
                        message=longrepr[:500],
                        traceback=longrepr,
                    )
                )

        return TestResultSchema(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            tests_total=total,
            tests_passed=passed,
            tests_failed=failing,
            tests_skipped=skipped,
            failure_summary=self._build_summary(failing_tests),
            failing_tests=failing_tests,
        )

    def _text_parse(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
    ) -> TestResultSchema:
        """Parse plain pytest text output."""
        passed = failed = skipped = 0

        match = _SUMMARY_PATTERN.search(stdout)
        if match:
            passed = int(match.group(1) or 0)
            failed = int(match.group(2) or 0)
            # group(3) = errored, group(4) = skipped
            skipped = int(match.group(4) or 0)
            dur = float(match.group(5) or duration_seconds)
            duration_seconds = dur

        total = passed + failed + skipped

        # Extract failing test names
        failing_tests = []
        for m in _FAILED_LINE.finditer(stdout):
            node_id = m.group(1).strip()
            msg = m.group(2) or ""
            # Try to find error type from surrounding context
            surrounding = stdout[max(0, stdout.find(node_id) - 200): stdout.find(node_id) + 500]
            error_type = self._extract_error_type(surrounding)
            failing_tests.append(
                FailingTestSchema(
                    name=node_id,
                    error_type=error_type,
                    message=msg[:300],
                    traceback=surrounding,
                )
            )

        return TestResultSchema(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            tests_total=total or None,
            tests_passed=passed or None,
            tests_failed=failed or None,
            tests_skipped=skipped or None,
            failure_summary=self._build_summary(failing_tests),
            failing_tests=failing_tests,
        )

    def _extract_error_type(self, text: str) -> str:
        m = _ERROR_TYPE.search(text)
        return m.group(1) if m else "UnknownError"

    def _build_summary(self, failing_tests: list[FailingTestSchema]) -> str | None:
        if not failing_tests:
            return None
        lines = [f"{t.name}: {t.error_type} — {t.message[:100]}" for t in failing_tests[:5]]
        if len(failing_tests) > 5:
            lines.append(f"... and {len(failing_tests) - 5} more")
        return "\n".join(lines)


# Singleton
test_result_parser = TestResultParser()
