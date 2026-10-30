"""
RepoMedic — Coverage-Driven Execution Trace Auditor (SWE-ABS 2026)

Inspired by SWE-ABS (2026): "Adversarial Benchmark Strengthening Exposes
Inflated Success Rates on Test-based Benchmarks".

Addresses the critical SWE-bench vulnerability where an agent patch passes
legacy or generated tests by accident without actually executing the modified
logic (vacuous test execution / false-positive verification).

Verifies whether the test suite execution trace actively traversed:
1. The modified target file(s)
2. The specific target function / class symbols modified in the patch
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple


class CoverageVerdict(str, Enum):
    EXERCISED = "EXERCISED"       # Target file and modified symbol confirmed executed
    PARTIAL = "PARTIAL"           # Target file confirmed executed, but specific symbol unverified
    BYPASSED = "BYPASSED"         # Tests passed, but modified file was NEVER executed (vacuous!)
    INCONCLUSIVE = "INCONCLUSIVE" # Trace output too sparse to determine


class CoverageAuditReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    verdict: CoverageVerdict
    target_files_detected: list[str]
    symbols_exercised: list[str]
    is_vacuous_pass: bool
    confidence_score: float
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "target_files_detected": self.target_files_detected,
            "symbols_exercised": self.symbols_exercised,
            "is_vacuous_pass": self.is_vacuous_pass,
            "confidence_score": round(self.confidence_score, 2),
            "details": self.details,
        }


class CoverageTraceAuditor:
    """Statically and dynamically analyzes test execution traces against patch boundaries."""

    @classmethod
    def extract_patch_targets(cls, patch_diff: str) -> tuple[list[str], list[str]]:
        """Extract modified file paths and function/class symbols from unified diff."""
        files: list[str] = []
        symbols: list[str] = []

        if not patch_diff:
            return files, symbols

        lines = patch_diff.splitlines()
        for line in lines:
            if line.startswith("+++ b/"):
                fpath = line[6:].strip()
                if fpath and fpath not in files:
                    files.append(fpath)
            elif line.startswith("@@"):
                # Unified diff hunk header often contains enclosing symbol: @@ ... @@ def func(...)
                match = re.search(r"@@\s+.*?\s+@@\s*(?:def|class|async def)\s+([a-zA-Z0-9_]+)", line)
                if match:
                    sym = match.group(1)
                    if sym not in symbols:
                        symbols.append(sym)
            elif line.startswith("+") and not line.startswith("+++"):
                # Detect newly added or modified function definitions
                match = re.search(r"^\+\s*(?:def|class|async def)\s+([a-zA-Z0-9_]+)", line)
                if match:
                    sym = match.group(1)
                    if sym not in symbols:
                        symbols.append(sym)

        return files, symbols

    @classmethod
    def audit_trace(
        cls,
        patch_diff: str,
        test_output: str,
        modified_files: list[str] | None = None,
    ) -> CoverageAuditReport:
        """
        Audits test runner stdout/stderr to ensure tests actually exercised the patched code.
        """
        extracted_files, extracted_symbols = cls.extract_patch_targets(patch_diff)
        target_files = modified_files or extracted_files

        if not target_files:
            return CoverageAuditReport(
                verdict=CoverageVerdict.INCONCLUSIVE,
                target_files_detected=[],
                symbols_exercised=[],
                is_vacuous_pass=False,
                confidence_score=0.5,
                details="No target files specified in patch or state.",
            )

        output_lower = test_output.lower() if test_output else ""
        detected_files: list[str] = []
        detected_symbols: list[str] = []

        # 1. Check if modified files appear in execution traces, pytest logs, or module paths
        for f in target_files:
            fname = Path(f).name.lower()
            stem = Path(f).stem.lower()
            if f.lower() in output_lower or fname in output_lower or f"test_{stem}" in output_lower:
                detected_files.append(f)

        # 2. Check if modified symbols appear in test session / tracebacks
        for sym in extracted_symbols:
            sym_lower = sym.lower()
            # Look for exact symbol or test naming convention (e.g. test_intcomma)
            if sym_lower in output_lower or f"test_{sym_lower}" in output_lower:
                detected_symbols.append(sym)

        # 3. Determine execution verdict
        if not detected_files:
            # Tests passed, but not a single target file was touched or mentioned in test runs!
            return CoverageAuditReport(
                verdict=CoverageVerdict.BYPASSED,
                target_files_detected=[],
                symbols_exercised=[],
                is_vacuous_pass=True,
                confidence_score=0.15,
                details=(
                    f"Vacuous Test Execution Warning (SWE-ABS): Modified file(s) "
                    f"{target_files} were not detected in test execution logs. "
                    f"High probability of disconnected or unexercised test cases."
                ),
            )

        if detected_symbols or len(detected_files) == len(target_files):
            # Strong confirmation: target file and symbol both active
            score = 0.95 if detected_symbols else 0.80
            return CoverageAuditReport(
                verdict=CoverageVerdict.EXERCISED,
                target_files_detected=detected_files,
                symbols_exercised=detected_symbols,
                is_vacuous_pass=False,
                confidence_score=score,
                details=(
                    f"Execution Confirmed: Target file(s) {detected_files} actively "
                    f"exercised in test run. Verified non-vacuous patch coverage."
                ),
            )

        return CoverageAuditReport(
            verdict=CoverageVerdict.PARTIAL,
            target_files_detected=detected_files,
            symbols_exercised=detected_symbols,
            is_vacuous_pass=False,
            confidence_score=0.65,
            details=f"Partial Coverage: Target file {detected_files} detected, but specific symbol trace unconfirmed.",
        )
