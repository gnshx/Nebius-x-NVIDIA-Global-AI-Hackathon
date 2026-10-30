"""Deterministic Patch Canonicalizer.

Grounding: CanonicalPatch: Reducing Reviewer Cognitive Load and Merge Friction
in AI-Assisted Software Engineering (FSE 2026) & Deterministic Formatting Invariants for SWE-bench (2026).

Problem:
LLM-generated candidate diffs frequently place imports in arbitrary order, introduce
spurious blank line fluctuations, and contain trailing whitespace. When submitted to open-source
repositories with pre-commit CI enforcement (ruff, isort, black), these cosmetic discrepancies
cause test-suite rejections and merge conflicts with maintainer PRs.

Solution:
DeterministicPatchCanonicalizer normalizes unified diff hunks:
1. Canonical Import Reordering: Groups newly added imports into standard library,
   third-party, and local tiers, sorting each tier alphabetically according to PEP 8 / isort.
2. Trailing Whitespace Stripping: Prunes trailing whitespace from newly added lines (+).
3. Consecutive Blank Normalization: Collapses excessive consecutive added empty lines.
4. Diff Reconstruction: Emits deterministic, minimal diff representations to collapse
   redundant candidate repair spaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


STDLIB_MODULES = {
    "abc", "argparse", "ast", "asyncio", "collections", "contextlib", "copy",
    "dataclasses", "datetime", "enum", "functools", "glob", "hashlib", "hmac",
    "inspect", "io", "itertools", "json", "logging", "math", "os", "pathlib",
    "pickle", "random", "re", "shutil", "signal", "socket", "sqlite3", "string",
    "struct", "subprocess", "sys", "tempfile", "threading", "time", "traceback",
    "typing", "unittest", "urllib", "uuid", "weakref", "zipfile"
}


@dataclass
class CanonicalPatchReport:
    """Report detailing patch canonicalization and structural normalization."""
    original_diff: str
    canonical_diff: str
    has_modifications: bool
    imports_sorted_count: int = 0
    whitespace_cleanups_count: int = 0
    blank_lines_normalized_count: int = 0

    def to_dict(self) -> dict:
        return {
            "has_modifications": self.has_modifications,
            "imports_sorted_count": self.imports_sorted_count,
            "whitespace_cleanups_count": self.whitespace_cleanups_count,
            "blank_lines_normalized_count": self.blank_lines_normalized_count,
            "diff_length_delta": len(self.canonical_diff) - len(self.original_diff),
        }


class DeterministicPatchCanonicalizer:
    """Normalizes candidate diffs into deterministic PEP 8 compliant representations."""

    def __init__(self) -> None:
        pass

    @classmethod
    def canonicalize(cls, diff_text: str) -> CanonicalPatchReport:
        """Class method convenience to canonicalize a unified diff string."""
        return cls().canonicalize_diff(diff_text)

    def canonicalize_diff(self, diff_text: str) -> CanonicalPatchReport:
        """Processes unified diff text and returns canonicalized diff."""
        if not diff_text.strip():
            return CanonicalPatchReport(
                original_diff=diff_text,
                canonical_diff=diff_text,
                has_modifications=False,
            )

        lines = diff_text.splitlines()
        output_lines: List[str] = []
        hunk_lines: List[str] = []
        in_hunk = False

        imports_sorted = 0
        whitespace_cleanups = 0
        blank_normalized = 0

        for line in lines:
            if line.startswith("@@"):
                if in_hunk:
                    proc_hunk, s_imp, w_clean, b_norm = self._process_hunk(hunk_lines)
                    output_lines.extend(proc_hunk)
                    imports_sorted += s_imp
                    whitespace_cleanups += w_clean
                    blank_normalized += b_norm
                    hunk_lines = []
                in_hunk = True
                output_lines.append(line)
            elif in_hunk:
                hunk_lines.append(line)
            else:
                # Diff headers (---, +++, diff --git)
                output_lines.append(line)

        if in_hunk and hunk_lines:
            proc_hunk, s_imp, w_clean, b_norm = self._process_hunk(hunk_lines)
            output_lines.extend(proc_hunk)
            imports_sorted += s_imp
            whitespace_cleanups += w_clean
            blank_normalized += b_norm

        canonical_diff = "\n".join(output_lines)
        modified = canonical_diff != diff_text

        return CanonicalPatchReport(
            original_diff=diff_text,
            canonical_diff=canonical_diff,
            has_modifications=modified,
            imports_sorted_count=imports_sorted,
            whitespace_cleanups_count=whitespace_cleanups,
            blank_lines_normalized_count=blank_normalized,
        )

    def _process_hunk(self, lines: List[str]) -> Tuple[List[str], int, int, int]:
        """Canonicalizes added lines inside a single hunk."""
        result: List[str] = []
        added_imports: List[str] = []
        import_insertion_idx: Optional[int] = None
        imports_sorted = 0
        whitespace_cleanups = 0
        blank_normalized = 0
        prev_was_blank_add = False

        for line in lines:
            if line.startswith("+"):
                # Clean trailing whitespace
                cleaned = line.rstrip()
                if len(cleaned) < len(line):
                    whitespace_cleanups += 1
                line = cleaned

                # Consecutive blank added lines check
                if line == "+":
                    if prev_was_blank_add:
                        blank_normalized += 1
                        continue  # Skip redundant blank line
                    prev_was_blank_add = True
                else:
                    prev_was_blank_add = False

                # Check if it is an added import
                if self._is_import_line(line[1:].strip()):
                    if import_insertion_idx is None:
                        import_insertion_idx = len(result)
                    added_imports.append(line[1:].strip())
                    continue
            else:
                prev_was_blank_add = False

            result.append(line)

        # If added imports exist, sort and insert them canonicalized
        if added_imports and import_insertion_idx is not None:
            sorted_imp_lines = self._sort_imports(added_imports)
            if sorted_imp_lines != added_imports:
                imports_sorted = len(added_imports)
            for imp in reversed(sorted_imp_lines):
                result.insert(import_insertion_idx, f"+{imp}")

        return result, imports_sorted, whitespace_cleanups, blank_normalized

    def _is_import_line(self, text: str) -> bool:
        """Determines if a code line is an import statement."""
        return text.startswith("import ") or text.startswith("from ")

    def _classify_import(self, imp_line: str) -> int:
        """Classifies import into 0: stdlib, 1: third-party, 2: local/relative."""
        if imp_line.startswith("from .") or imp_line.startswith("import ."):
            return 2

        # Extract root module
        match = re.match(r"(?:from|import)\s+([a-zA-Z0-9_]+)", imp_line)
        if match:
            root = match.group(1)
            if root in STDLIB_MODULES:
                return 0
            if root in ("services", "agents", "models", "db", "config", "routes"):
                return 2

        return 1

    def _sort_imports(self, imports: List[str]) -> List[str]:
        """Sorts imports according to PEP 8 / isort standards (stdlib -> 3rd-party -> local)."""
        unique_imports = sorted(list(set(imports)), key=lambda x: (self._classify_import(x), x.lower()))
        return unique_imports
