"""
RepoMedic — Traceback Distiller & Fault Localization Isolator

Implements fault localization and context pruning from:
- Reasoning-Guided Fault Localization (RGFL) for Repository-Level Coding Agents (2026)
- Trace-Driven Iterative Repair (DynaFix, 2026)

Solves the critical "Traceback Poisoning" failure mode where LLMs are distracted by 15-20
internal runner/stdlib frames (e.g. pytest, pluggy, python3.10/site-packages) instead of
focusing on the exact repository-local culprit function.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)

# Pattern for Python traceback frames: File "...", line 123, in func_name
_FRAME_PATTERN = re.compile(
    r'^\s*File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+([a-zA-Z0-9_<>\.]+)(?:\n\s*(.+))?$',
    re.MULTILINE,
)

# Standard internal libraries to collapse
_INTERNAL_MARKERS = [
    "/lib/python", "/usr/lib", "site-packages/pytest",
    "_pytest", "pluggy", "site-packages/unittest",
    "execnet", "site-packages/pip", "<frozen ",
]


class DistilledFrame(NamedTuple):
    __test__ = False
    file_path: str
    line_number: int
    function_name: str
    code_line: str
    frame_type: str  # "REPO_LOCAL" | "TEST_LOCAL" | "EXTERNAL"


class DistilledTracebackResult(NamedTuple):
    __test__ = False
    distilled_traceback: str
    culprit_file: str | None
    culprit_line: int | None
    culprit_function: str | None
    repo_frames_count: int
    omitted_frames_count: int
    compression_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "distilled_traceback": self.distilled_traceback,
            "culprit_file": self.culprit_file,
            "culprit_line": self.culprit_line,
            "culprit_function": self.culprit_function,
            "repo_frames_count": self.repo_frames_count,
            "omitted_frames_count": self.omitted_frames_count,
            "compression_ratio": self.compression_ratio,
        }


class TracebackDistiller:
    """Distills raw multi-frame execution tracebacks into repo-local diagnostic insights."""

    @classmethod
    def classify_frame(cls, path: str, repo_keywords: list[str] | None = None) -> str:
        """Categorize a stack frame path."""
        p_lower = path.lower()
        if any(marker in p_lower for marker in _INTERNAL_MARKERS):
            return "EXTERNAL"
        if "test" in p_lower:
            return "TEST_LOCAL"
        if repo_keywords and any(kw.lower() in p_lower for kw in repo_keywords):
            return "REPO_LOCAL"
        if "site-packages" in p_lower:
            return "EXTERNAL"
        return "REPO_LOCAL"

    @classmethod
    def distill(
        cls,
        raw_traceback: str,
        repo_keywords: list[str] | None = None,
    ) -> DistilledTracebackResult:
        """
        Parses a traceback, collapsing internal runtime frames while highlighting repository culprit sites.
        """
        if not raw_traceback:
            return DistilledTracebackResult(
                distilled_traceback="",
                culprit_file=None,
                culprit_line=None,
                culprit_function=None,
                repo_frames_count=0,
                omitted_frames_count=0,
                compression_ratio=0.0,
            )

        orig_len = max(1, len(raw_traceback))
        frames: list[DistilledFrame] = []

        for match in _FRAME_PATTERN.finditer(raw_traceback):
            path = match.group(1).strip()
            line_no = int(match.group(2))
            func = match.group(3).strip()
            code = (match.group(4) or "").strip()
            frame_type = cls.classify_frame(path, repo_keywords)
            frames.append(DistilledFrame(path, line_no, func, code, frame_type))

        if not frames:
            # Fallback if non-standard traceback format
            return DistilledTracebackResult(
                distilled_traceback=raw_traceback[:1500],
                culprit_file=None,
                culprit_line=None,
                culprit_function=None,
                repo_frames_count=0,
                omitted_frames_count=0,
                compression_ratio=0.0,
            )

        # Identify culprit site (last REPO_LOCAL frame before crash)
        repo_frames = [f for f in frames if f.frame_type == "REPO_LOCAL"]
        culprit = repo_frames[-1] if repo_frames else frames[-1]

        distilled_lines: list[str] = ["Traceback (distilled repo-local fault path):"]
        omitted_streak = 0
        repo_count = 0
        total_omitted = 0

        for f in frames:
            if f.frame_type in ("REPO_LOCAL", "TEST_LOCAL"):
                if omitted_streak > 0:
                    distilled_lines.append(f"  ... [{omitted_streak} internal runtime / test-runner frame(s) omitted] ...")
                    total_omitted += omitted_streak
                    omitted_streak = 0

                tag = "[TARGET REPO]" if f.frame_type == "REPO_LOCAL" else "[TEST HARNESS]"
                distilled_lines.append(f'  {tag} File "{f.file_path}", line {f.line_number}, in {f.function_name}')
                if f.code_line:
                    distilled_lines.append(f"    > {f.code_line}")
                repo_count += 1
            else:
                omitted_streak += 1

        if omitted_streak > 0:
            distilled_lines.append(f"  ... [{omitted_streak} internal runtime / test-runner frame(s) omitted] ...")
            total_omitted += omitted_streak

        # Extract trailing exception message
        last_lines = [l.strip() for l in raw_traceback.splitlines() if l.strip()]
        if last_lines and not last_lines[-1].startswith("File "):
            distilled_lines.append(f"Crash Exception: {last_lines[-1]}")

        distilled_text = "\n".join(distilled_lines)
        comp_ratio = round(max(0.0, 1.0 - (len(distilled_text) / orig_len)), 3)

        logger.info(
            "traceback_distillation_complete",
            culprit_file=culprit.file_path,
            culprit_line=culprit.line_number,
            culprit_func=culprit.function_name,
            repo_frames=repo_count,
            omitted_frames=total_omitted,
            comp_ratio=comp_ratio,
        )

        return DistilledTracebackResult(
            distilled_traceback=distilled_text,
            culprit_file=culprit.file_path,
            culprit_line=culprit.line_number,
            culprit_function=culprit.function_name,
            repo_frames_count=repo_count,
            omitted_frames_count=total_omitted,
            compression_ratio=comp_ratio,
        )
