"""
RepoMedic — Selective Hunk Auditor & Granular Stager (CodeMonkeys / DeepSWE 2026)

Decomposes unified multi-hunk diffs into individual syntactic hunks:
1. Categorizes hunks: SEMANTIC_LOGIC, TEST_ASSERTION, COSMETIC_WHITESPACE, COMMENT_ONLY, IMPORT_STATEMENT.
2. Identifies and strips pure cosmetic churn, trailing whitespace edits, and accidental comment mutations.
3. Produces a minimal, parsimonious staged diff that preserves semantic logic while eliminating review noise.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)

HUNK_HEADER_PATTERN = re.compile(r"^@@\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@(.*)$")


class HunkMetadata(NamedTuple):
    __test__ = False  # Prevent pytest collection

    index: int
    header: str
    category: str  # "SEMANTIC_LOGIC" | "TEST_ASSERTION" | "COSMETIC_WHITESPACE" | "COMMENT_ONLY" | "IMPORT_STATEMENT"
    added_lines_count: int
    deleted_lines_count: int
    is_essential: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "header": self.header,
            "category": self.category,
            "added_lines_count": self.added_lines_count,
            "deleted_lines_count": self.deleted_lines_count,
            "is_essential": self.is_essential,
            "rationale": self.rationale,
        }


class HunkAuditReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    total_hunks: int
    essential_hunks: int
    cosmetic_hunks: int
    parsimony_ratio: float
    staged_diff: str
    hunk_details: list[HunkMetadata]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_hunks": self.total_hunks,
            "essential_hunks": self.essential_hunks,
            "cosmetic_hunks": self.cosmetic_hunks,
            "parsimony_ratio": self.parsimony_ratio,
            "staged_diff": self.staged_diff,
            "hunk_details": [h.to_dict() for h in self.hunk_details],
        }


class SelectiveHunkAuditor:
    """Audits and filters patch hunks to eliminate accidental cosmetic churn and preserve core fixes."""

    @classmethod
    def audit_and_stage_diff(cls, full_diff: str, file_path: str = "") -> HunkAuditReport:
        """Decomposes a unified diff into categorized hunks and stages only essential hunks."""
        if not full_diff or not full_diff.strip():
            return HunkAuditReport(
                total_hunks=0,
                essential_hunks=0,
                cosmetic_hunks=0,
                parsimony_ratio=1.0,
                staged_diff="",
                hunk_details=[],
            )

        lines = full_diff.splitlines()
        file_header_lines: list[str] = []
        raw_hunks: list[tuple[str, list[str]]] = []
        current_hunk_header = ""
        current_hunk_lines: list[str] = []

        # Parse unified diff header vs hunks
        for line in lines:
            if line.startswith("@@"):
                if current_hunk_header:
                    raw_hunks.append((current_hunk_header, current_hunk_lines))
                current_hunk_header = line
                current_hunk_lines = []
            elif not current_hunk_header:
                file_header_lines.append(line)
            else:
                current_hunk_lines.append(line)

        if current_hunk_header:
            raw_hunks.append((current_hunk_header, current_hunk_lines))

        hunk_details: list[HunkMetadata] = []
        staged_hunks_output: list[str] = []

        is_test_file = "test" in file_path.lower()

        for idx, (header, hunk_body) in enumerate(raw_hunks):
            metadata, clean_body = cls._evaluate_hunk(idx, header, hunk_body, is_test_file)
            hunk_details.append(metadata)

            if metadata.is_essential:
                staged_hunks_output.append(header)
                staged_hunks_output.extend(clean_body)

        essential_count = sum(1 for h in hunk_details if h.is_essential)
        cosmetic_count = sum(1 for h in hunk_details if not h.is_essential)
        total_count = len(hunk_details)

        parsimony_ratio = round(
            (essential_count / max(1, total_count)), 2
        )

        # Build clean staged diff
        if essential_count > 0:
            staged_diff = "\n".join(file_header_lines + staged_hunks_output)
            if not staged_diff.endswith("\n"):
                staged_diff += "\n"
        else:
            staged_diff = ""

        logger.info(
            "selective_hunk_audit_completed",
            file_path=file_path,
            total_hunks=total_count,
            essential=essential_count,
            cosmetic=cosmetic_count,
            parsimony_ratio=parsimony_ratio,
        )

        return HunkAuditReport(
            total_hunks=total_count,
            essential_hunks=essential_count,
            cosmetic_hunks=cosmetic_count,
            parsimony_ratio=parsimony_ratio,
            staged_diff=staged_diff,
            hunk_details=hunk_details,
        )

    @classmethod
    def _evaluate_hunk(
        cls,
        idx: int,
        header: str,
        lines: list[str],
        is_test_file: bool,
    ) -> tuple[HunkMetadata, list[str]]:
        added_lines = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]
        deleted_lines = [l[1:] for l in lines if l.startswith("-") and not l.startswith("---")]

        # Case 1: Pure whitespace change
        added_non_ws = [l.strip() for l in added_lines if l.strip()]
        deleted_non_ws = [l.strip() for l in deleted_lines if l.strip()]

        if not added_non_ws and not deleted_non_ws:
            return (
                HunkMetadata(
                    index=idx,
                    header=header,
                    category="COSMETIC_WHITESPACE",
                    added_lines_count=len(added_lines),
                    deleted_lines_count=len(deleted_lines),
                    is_essential=False,
                    rationale="Hunk contains only empty line or whitespace modifications.",
                ),
                lines,
            )

        # If added lines and deleted lines have exact same text stripped of whitespace
        if added_non_ws == deleted_non_ws:
            return (
                HunkMetadata(
                    index=idx,
                    header=header,
                    category="COSMETIC_WHITESPACE",
                    added_lines_count=len(added_lines),
                    deleted_lines_count=len(deleted_lines),
                    is_essential=False,
                    rationale="Hunk contains re-indentation or whitespace reformatting without semantic change.",
                ),
                lines,
            )

        # Case 2: Comment-only modifications
        added_code = [l for l in added_non_ws if not l.startswith("#") and not l.startswith("//") and not l.startswith("/*")]
        deleted_code = [l for l in deleted_non_ws if not l.startswith("#") and not l.startswith("//") and not l.startswith("/*")]

        if not added_code and not deleted_code:
            return (
                HunkMetadata(
                    index=idx,
                    header=header,
                    category="COMMENT_ONLY",
                    added_lines_count=len(added_lines),
                    deleted_lines_count=len(deleted_lines),
                    is_essential=False,
                    rationale="Hunk modifies comments only without altering runtime code execution.",
                ),
                lines,
            )

        # Case 3: Import statements
        is_import = all(
            l.startswith("import ") or l.startswith("from ")
            for l in added_non_ws
        ) if added_non_ws else False

        if is_import:
            return (
                HunkMetadata(
                    index=idx,
                    header=header,
                    category="IMPORT_STATEMENT",
                    added_lines_count=len(added_lines),
                    deleted_lines_count=len(deleted_lines),
                    is_essential=True,
                    rationale="Hunk introduces module dependencies required for patch execution.",
                ),
                lines,
            )

        # Case 4: Test Assertion
        if is_test_file or any("assert " in l or "pytest.raises" in l or "expect(" in l for l in added_non_ws):
            return (
                HunkMetadata(
                    index=idx,
                    header=header,
                    category="TEST_ASSERTION",
                    added_lines_count=len(added_lines),
                    deleted_lines_count=len(deleted_lines),
                    is_essential=True,
                    rationale="Hunk synthesizes or amends verification test assertions.",
                ),
                lines,
            )

        # Case 5: Semantic logic
        return (
            HunkMetadata(
                index=idx,
                header=header,
                category="SEMANTIC_LOGIC",
                added_lines_count=len(added_lines),
                deleted_lines_count=len(deleted_lines),
                is_essential=True,
                rationale="Hunk alters control flow, variable bindings, or business logic.",
            ),
            lines,
        )
