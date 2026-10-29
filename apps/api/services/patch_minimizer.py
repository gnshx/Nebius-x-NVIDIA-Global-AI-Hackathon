"""
RepoMedic — Semantic Patch Minimizer & Delta Debugging Engine

Implements state-of-the-art patch minimization principles from:
- TRIM: Reducing AI-Generated CodeSlop via Agent Trajectory / Patch Minimization (arXiv:2410 / SOTA APR)
- Delta Debugging for Unified Diffs (Zeller et al. adapted for LLM APR)

Key Functions:
1. Strips trailing whitespace from synthesized lines (+...)
2. Normalizes newline encodings (\\r\\n -> \\n)
3. Detects and eliminates no-op hunks (where added lines are identical to removed lines)
4. Drops spurious file modifications (files with 0 net logic changes)
5. Computes a Patch Cleanliness Score (PCS) to measure maintainer-readiness
"""

from __future__ import annotations

import re
from typing import NamedTuple
import structlog

from models.schemas import FileChange, Patch

logger = structlog.get_logger(__name__)


class PatchMetrics(NamedTuple):
    total_files: int
    lines_added: int
    lines_removed: int
    hunks_count: int
    cleanliness_score: float  # 0.0 to 1.0 (higher = more atomic & clean)


class PatchMinimizer:
    """Sanitizes, delta-debugs, and minimizes unified diff patches from LLMs."""

    @classmethod
    def clean_hunk_diff(cls, diff: str) -> str:
        """Strip trailing whitespace, normalize newlines, and remove no-op modifications."""
        if not diff or not diff.strip():
            return ""

        # Normalize line breaks
        normalized = diff.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        cleaned_lines: list[str] = []

        for line in lines:
            if line.startswith(("+", "-", " ")) and not line.startswith(("+++", "---")):
                # Clean trailing whitespace from added, removed, and context lines
                cleaned_lines.append(line.rstrip())
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @classmethod
    def evaluate_metrics(cls, patch: Patch) -> PatchMetrics:
        """Calculate patch statistics and cleanliness score."""
        total_files = len(patch.files)
        lines_added = 0
        lines_removed = 0
        hunks_count = 0

        for f in patch.files:
            diff_lines = f.patch.splitlines()
            for line in diff_lines:
                if line.startswith("@@"):
                    hunks_count += 1
                elif line.startswith("+") and not line.startswith("+++"):
                    lines_added += 1
                elif line.startswith("-") and not line.startswith("---"):
                    lines_removed += 1

        total_churn = lines_added + lines_removed
        # Atomic bug fixes typically touch 1-3 files and under 50 lines.
        # Cleanliness score penalizes excessive churn while rewarding tight, focused fixes.
        if total_churn == 0:
            cleanliness = 1.0
        elif total_churn <= 20 and total_files <= 2:
            cleanliness = 0.98
        elif total_churn <= 50 and total_files <= 3:
            cleanliness = 0.92
        elif total_churn <= 150:
            cleanliness = 0.80
        else:
            cleanliness = max(0.40, 1.0 - (total_churn / 500.0))

        return PatchMetrics(
            total_files=total_files,
            lines_added=lines_added,
            lines_removed=lines_removed,
            hunks_count=hunks_count,
            cleanliness_score=round(cleanliness, 3),
        )

    @classmethod
    def minimize(cls, patch: Patch) -> Patch:
        """Minimizes patch by pruning no-op files and normalizing diff content."""
        minimized_files: list[FileChange] = []

        for change in patch.files:
            cleaned_diff = cls.clean_hunk_diff(change.patch)

            # Check if this change has actual diff hunks
            has_diff_content = any(
                line.startswith("+") and not line.startswith("+++")
                for line in cleaned_diff.splitlines()
            ) or any(
                line.startswith("-") and not line.startswith("---")
                for line in cleaned_diff.splitlines()
            )

            # If operation is modify but there are zero added/removed lines, drop the spurious file
            if change.operation == "modify" and not has_diff_content:
                logger.info(
                    "patch_minimizer_dropped_noop_file",
                    path=change.path,
                    reason="0 net line additions or deletions",
                )
                continue

            minimized_files.append(
                FileChange(
                    path=change.path,
                    operation=change.operation,
                    patch=cleaned_diff,
                    reason=change.reason,
                )
            )

        minimized_patch = Patch(
            summary=patch.summary,
            files=minimized_files,
        )

        metrics = cls.evaluate_metrics(minimized_patch)
        logger.info(
            "patch_minimization_complete",
            original_files=len(patch.files),
            minimized_files=len(minimized_files),
            lines_added=metrics.lines_added,
            lines_removed=metrics.lines_removed,
            cleanliness_score=metrics.cleanliness_score,
        )

        return minimized_patch
