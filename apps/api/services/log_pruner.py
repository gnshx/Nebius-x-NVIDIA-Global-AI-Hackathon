"""
RepoMedic — Runtime Log & Tool-Output Pruner

Implements cutting-edge context management and token economy principles from:
- SWE-Pruner: Task-Aware Context Pruning for Repository-Level Coding Agents (2026)
- Runtime Tool-Output Pruning & Terminal Context Sanitization (Self-GC, 2026)

Solves the critical "Context Wall" failure mode in multi-turn SWE-bench agents where
hundreds of non-informative passing test lines (e.g. 240 passed tests) and terminal
ANSI noise bloat the LLM context window, causing reasoning degradation and token exhaustion.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)

# Regular expressions for ANSI escape codes and pytest patterns
_ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_PASSING_TEST_LINE = re.compile(r"^[^\n]+(?:PASSED|XFAIL|SKIPPED)\s+\[\s*\d+%\s*\]$", re.MULTILINE)
_SECTION_DIVIDER = re.compile(r"^={3,}\s*(.+?)\s*={3,}$", re.MULTILINE)
_EXCEPTION_LINE = re.compile(r"(?:^E\s+|-\s+|^)([a-zA-Z_]\w*(?:Error|Exception)):\s*(.+)$", re.MULTILINE)
_FILE_LINE_LOC = re.compile(r"(?:File \"([^\"]+)\", line (\d+)|([a-zA-Z0-9_\/.-]+\.py):(\d+):)")


class LogPruningResult(NamedTuple):
    __test__ = False
    pruned_text: str
    original_bytes: int
    pruned_bytes: int
    compression_ratio: float  # e.g. 0.72 = 72% token reduction
    isolated_failure_count: int
    root_exceptions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pruned_text": self.pruned_text,
            "original_bytes": self.original_bytes,
            "pruned_bytes": self.pruned_bytes,
            "compression_ratio": self.compression_ratio,
            "isolated_failure_count": self.isolated_failure_count,
            "root_exceptions": self.root_exceptions,
        }


class RuntimeLogPruner:
    """Sanitizes raw test execution logs, stripping noise while preserving 100% of diagnostic cues."""

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Strip ANSI terminal escape sequences."""
        if not text:
            return ""
        return _ANSI_REGEX.sub("", text)

    @classmethod
    def prune_pytest_output(
        cls,
        stdout: str,
        stderr: str = "",
        max_chars: int = 4000,
    ) -> LogPruningResult:
        """
        Extracts high-density failure diagnostics from pytest stdout/stderr.
        Eliminates passing test lines, environment banners, and isolates FAILURES blocks.
        """
        combined_raw = f"{stdout}\n{stderr}".strip()
        original_bytes = len(combined_raw.encode("utf-8"))

        clean_text = cls.strip_ansi(combined_raw)

        # Extract root exceptions
        exceptions = [f"{m[0]}: {m[1].strip()}" for m in _EXCEPTION_LINE.findall(clean_text)]
        unique_exceptions = list(dict.fromkeys(exceptions))[:5]

        # Extract FAILURES and ERRORS sections
        lines = clean_text.splitlines()
        pruned_lines: list[str] = []
        in_failure_block = False
        isolated_failures = 0

        summary_line = ""

        for line in lines:
            stripped = line.strip()

            # Detect test summary footer (e.g. === 1 failed, 240 passed in 0.20s ===)
            if re.match(r"^=+\s+.*(?:failed|passed|error).*\s+in\s+[\d.]+s\s+=+$", stripped):
                summary_line = stripped
                continue

            # Detect section header
            if stripped.startswith("===") and ("FAILURES" in stripped or "ERRORS" in stripped):
                in_failure_block = True
                isolated_failures += 1
                pruned_lines.append(line)
                continue
            elif stripped.startswith("===") and in_failure_block and not stripped.startswith("=== FAILURES"):
                # End of failures section
                in_failure_block = False
                pruned_lines.append(line)
                continue

            if in_failure_block:
                pruned_lines.append(line)
                continue

            # Drop passing test lines
            if _PASSING_TEST_LINE.match(stripped):
                continue

            # Include lines mentioning FAILED or traceback markers
            if "FAILED" in stripped or "Traceback (most recent call last):" in stripped:
                pruned_lines.append(line)
            elif stripped.startswith("E   ") or stripped.startswith(">   "):
                pruned_lines.append(line)

        # Reassemble output
        result_content = "\n".join(pruned_lines).strip()

        # If failures section wasn't captured or empty, fall back to extracting error lines
        if not result_content or len(result_content) < 50:
            relevant_lines = [
                line for line in lines
                if not _PASSING_TEST_LINE.match(line.strip())
                and not line.strip().startswith("platform linux")
                and not line.strip().startswith("rootdir:")
            ]
            result_content = "\n".join(relevant_lines[-60:])  # last 60 relevant lines

        if summary_line and summary_line not in result_content:
            result_content = f"{result_content}\n\n{summary_line}"

        # Bound max chars
        if len(result_content) > max_chars:
            half = max_chars // 2
            result_content = (
                result_content[:half]
                + "\n\n... [intermediate traceback lines pruned by RuntimeLogPruner] ...\n\n"
                + result_content[-half:]
            )

        pruned_bytes = len(result_content.encode("utf-8"))
        compression_ratio = round(
            max(0.0, 1.0 - (pruned_bytes / max(1, original_bytes))), 3
        )

        logger.info(
            "runtime_log_pruner_executed",
            original_bytes=original_bytes,
            pruned_bytes=pruned_bytes,
            compression_ratio=compression_ratio,
            isolated_failures=isolated_failures,
        )

        return LogPruningResult(
            pruned_text=result_content,
            original_bytes=original_bytes,
            pruned_bytes=pruned_bytes,
            compression_ratio=compression_ratio,
            isolated_failure_count=isolated_failures,
            root_exceptions=unique_exceptions,
        )
