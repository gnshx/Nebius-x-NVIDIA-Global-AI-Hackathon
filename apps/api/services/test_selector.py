"""
RepoMedic — Test Impact Analysis (TIA) & Selective Test Execution Engine

Addresses the critical SWE-bench latency bottleneck:
Instead of running tens of thousands of tests across massive repositories
during every iteration of an agent's self-healing loop, TIA performs:
  1. Micro-feedback Stage: Runs the synthesized reproduction test.
  2. Impact-scoped Stage: Executes neighbor tests exercising the modified AST nodes.
  3. Full Regression Gate: Runs 100% of the repository test suite on final candidate.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Sequence


class TestImpactAnalyzer:
    """Calculates minimal test sets affected by code changes."""

    @staticmethod
    def extract_module_stem(filepath: str) -> str:
        """Extract primary module identifier from path. e.g. 'src/humanize/number.py' -> 'number'."""
        path = Path(filepath)
        stem = path.stem.lower()
        if stem.startswith("test_"):
            return stem[5:]
        if stem.endswith("_test"):
            return stem[:-5]
        return stem

    @classmethod
    def match_test_file(cls, source_file: str, test_file: str) -> bool:
        """Check if test_file is likely covering source_file."""
        source_stem = cls.extract_module_stem(source_file)
        test_stem = cls.extract_module_stem(test_file)

        if source_stem == test_stem:
            return True

        # Check sub-module prefix matching e.g. test_number_formatting.py for number.py
        if test_stem.startswith(f"{source_stem}_") or test_stem.endswith(f"_{source_stem}"):
            return True

        # Check path directory matching
        src_parts = [p.lower() for p in Path(source_file).parts if p not in ("src", "lib", "app")]
        test_parts = [p.lower() for p in Path(test_file).parts if p not in ("tests", "test")]

        return any(part in test_parts for part in src_parts if len(part) > 3)

    @classmethod
    def select_impacted_tests(
        cls,
        modified_files: Sequence[str],
        available_tests: Sequence[str],
    ) -> list[str]:
        """
        Return filtered list of test files impacted by modified source files.
        If no specific match is found, returns available_tests to maintain safety.
        """
        impacted: set[str] = set()

        for mod_file in modified_files:
            # If a test file was directly modified, include it immediately
            if "test" in mod_file.lower():
                impacted.add(mod_file)
                continue

            for test_file in available_tests:
                if cls.match_test_file(mod_file, test_file):
                    impacted.add(test_file)

        # Fallback: if no targeted tests match, run all available tests
        if not impacted and available_tests:
            return list(available_tests)

        return sorted(impacted)

    @classmethod
    def build_test_command(
        cls,
        impacted_tests: Sequence[str],
        verbose: bool = True,
        fail_fast: bool = False,
    ) -> str:
        """Build an optimized pytest execution command."""
        flags = ["-v"] if verbose else ["-q"]
        if fail_fast:
            flags.append("-x")
        flags.append("--tb=short")

        if not impacted_tests:
            return f"pytest {' '.join(flags)}"

        test_args = " ".join(impacted_tests)
        return f"pytest {' '.join(flags)} {test_args}"
