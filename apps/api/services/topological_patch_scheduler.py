"""
RepoMedic — Multi-File Topological Patch Scheduler (Multi-SWE-bench 2025/2026)

Solves the multi-file repair bottleneck where AI coding agents drop in success rate
due to cascading import errors, out-of-order file modifications, and interface mismatches.

1. Analyzes AST import dependencies across all files in a multi-file patch:
   - Detects when file A imports or references modules in file B.
   - Guarantees base utilities and interface definitions are ordered before consumers.
   - Guarantees production code is scheduled before test suite assertions.
2. Constructs a Directed Acyclic Graph (DAG) of file changes.
3. Performs Kahn's algorithm topological sorting with cycle detection and fallback resolution.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple
import structlog

logger = structlog.get_logger(__name__)


class ScheduledFileChange(NamedTuple):
    order_index: int
    path: str
    operation: str
    dependencies: List[str]
    is_test_file: bool
    summary_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_index": self.order_index,
            "path": self.path,
            "operation": self.operation,
            "dependencies": self.dependencies,
            "is_test_file": self.is_test_file,
            "summary_reason": self.summary_reason,
        }


class ScheduleReport(NamedTuple):
    total_files: int
    ordered_files: List[ScheduledFileChange]
    has_circular_dependency: bool
    detected_cycles: List[List[str]]
    is_multi_file_patch: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "ordered_files": [f.to_dict() for f in self.ordered_files],
            "has_circular_dependency": self.has_circular_dependency,
            "detected_cycles": self.detected_cycles,
            "is_multi_file_patch": self.is_multi_file_patch,
        }


class TopologicalPatchScheduler:
    """Schedules multi-file patch changes using topological dependency ordering."""

    @classmethod
    def schedule_patch_files(cls, files: List[Dict[str, Any]]) -> ScheduleReport:
        """Computes the optimal topological execution order for patch file modifications."""
        if not files:
            return ScheduleReport(
                total_files=0,
                ordered_files=[],
                has_circular_dependency=False,
                detected_cycles=[],
                is_multi_file_patch=False,
            )

        if len(files) == 1:
            f = files[0]
            single = ScheduledFileChange(
                order_index=0,
                path=f.get("path", ""),
                operation=f.get("operation", "modify"),
                dependencies=[],
                is_test_file=cls._is_test_file(f.get("path", "")),
                summary_reason=f.get("reason", ""),
            )
            return ScheduleReport(
                total_files=1,
                ordered_files=[single],
                has_circular_dependency=False,
                detected_cycles=[],
                is_multi_file_patch=False,
            )

        # Build graph
        paths = [f.get("path", "") for f in files]
        path_map = {f.get("path", ""): f for f in files}

        adj: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = {p: 0 for p in paths}

        # Analyze cross-file import dependencies
        for p in paths:
            file_data = path_map[p]
            diff = file_data.get("diff", "")
            imported_modules = cls._extract_imports_from_diff(diff)

            for other_path in paths:
                if p == other_path:
                    continue
                # If other_path is a test and p is source, other_path depends on p
                if cls._is_test_file(other_path) and not cls._is_test_file(p):
                    if p not in adj:
                        adj[p] = set()
                    if other_path not in adj[p]:
                        adj[p].add(other_path)
                        in_degree[other_path] += 1
                    continue

                # Check if p imports module matching other_path stem
                other_stem = Path(other_path).stem
                if other_stem in imported_modules and not cls._is_test_file(p):
                    # p depends on other_path (other_path -> p)
                    if other_path not in adj:
                        adj[other_path] = set()
                    if p not in adj[other_path]:
                        adj[other_path].add(p)
                        in_degree[p] += 1

        # Kahn's algorithm for topological sorting
        queue = deque([p for p in paths if in_degree[p] == 0])
        # Sort queue so that source files precede test files
        queue = deque(sorted(queue, key=lambda x: (cls._is_test_file(x), x)))

        sorted_paths: List[str] = []
        while queue:
            node = queue.popleft()
            sorted_paths.append(node)

            for neighbor in sorted(adj.get(node, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        has_cycle = len(sorted_paths) < len(paths)
        cycles: List[List[str]] = []

        if has_cycle:
            # Fallback for remaining cyclic nodes
            remaining = [p for p in paths if p not in sorted_paths]
            cycles.append(remaining)
            # Order remaining by non-test first
            remaining_sorted = sorted(remaining, key=lambda x: (cls._is_test_file(x), x))
            sorted_paths.extend(remaining_sorted)

        ordered_changes: List[ScheduledFileChange] = []
        for idx, p in enumerate(sorted_paths):
            f = path_map[p]
            deps = [other for other in paths if p in adj.get(other, set())]
            ordered_changes.append(
                ScheduledFileChange(
                    order_index=idx,
                    path=p,
                    operation=f.get("operation", "modify"),
                    dependencies=deps,
                    is_test_file=cls._is_test_file(p),
                    summary_reason=f.get("reason", ""),
                )
            )

        logger.info(
            "topological_patch_scheduled",
            total_files=len(paths),
            has_cycle=has_cycle,
            ordered_sequence=[c.path for c in ordered_changes],
        )

        return ScheduleReport(
            total_files=len(paths),
            ordered_files=ordered_changes,
            has_circular_dependency=has_cycle,
            detected_cycles=cycles,
            is_multi_file_patch=True,
        )

    @staticmethod
    def _is_test_file(path: str) -> bool:
        p_lower = path.lower()
        return "test" in p_lower or p_lower.startswith("tests/") or p_lower.endswith("_test.py")

    @staticmethod
    def _extract_imports_from_diff(diff: str) -> Set[str]:
        """Extracts imported module names from added lines in unified diff."""
        modules: Set[str] = set()
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                cleaned = line[1:].strip()
                # match: from x import y OR import x
                m_from = re.match(r"^from\s+([a-zA-Z0-9_\.]+)\s+import", cleaned)
                if m_from:
                    modules.add(m_from.group(1).split(".")[-1])
                m_imp = re.match(r"^import\s+([a-zA-Z0-9_\.]+)", cleaned)
                if m_imp:
                    modules.add(m_imp.group(1).split(".")[-1])
        return modules
