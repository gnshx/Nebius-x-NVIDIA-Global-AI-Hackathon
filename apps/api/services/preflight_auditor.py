"""
RepoMedic — Adversarial Pre-Flight Patch Auditor

Implements pre-sandbox validation from:
- PROBE: Behavioral Probing & Invariant Consensus in Automated Program Repair (2026)
- Pre-Flight Defect Isolation in Autonomous Agentic Engineering

Conducts static and heuristic pre-flight auditing on candidate patches before
allocating container execution sandbox resources:
1. Detects debugging leftovers (e.g. `breakpoint()`, `import pdb`, `print(...)`).
2. Detects generic unhandled exception raises (e.g. `raise Exception()`).
3. Evaluates overall pre-flight risk level ("LOW" | "MEDIUM" | "HIGH").
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class PreflightAuditReport(NamedTuple):
    __test__ = False
    is_sandbox_ready: bool
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"
    issues_detected: list[str]
    clean_lines_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_sandbox_ready": self.is_sandbox_ready,
            "risk_level": self.risk_level,
            "issues_detected": self.issues_detected,
            "clean_lines_ratio": self.clean_lines_ratio,
        }


class AdversarialPreflightAuditor:
    """Audits patch diffs for debugging artifacts and anti-patterns before sandbox admission."""

    # Heuristics for debug artifacts and anti-patterns
    DEBUG_PATTERNS = [
        (re.compile(r"^\+\s*breakpoint\s*\(\s*\)", re.MULTILINE), "Leftover breakpoint() call"),
        (re.compile(r"^\+\s*(?:import\s+pdb|import\s+ipdb)", re.MULTILINE), "Leftover debugger import (pdb/ipdb)"),
        (re.compile(r"^\+\s*print\s*\(", re.MULTILINE), "Leftover print() statement in production diff"),
        (re.compile(r"^\+\s*raise\s+Exception\s*\(", re.MULTILINE), "Generic unspecific raise Exception() instead of typed exception"),
    ]

    @classmethod
    def audit_patch(cls, files: list[dict[str, Any]]) -> PreflightAuditReport:
        """Audits file diffs before sandbox execution."""
        issues: list[str] = []
        total_added_lines = 0
        debug_lines_count = 0

        for f in files:
            path = f.get("path", "")
            diff = f.get("diff", "") or f.get("patch", "") or ""
            is_test_file = "test" in path.lower()

            added_lines = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
            total_added_lines += len(added_lines)

            # Check debug patterns (skip print checks for test files)
            for pattern, msg in cls.DEBUG_PATTERNS:
                if "print" in msg and is_test_file:
                    continue
                matches = pattern.findall(diff)
                if matches:
                    issues.append(f"[{path}] {msg} ({len(matches)} occurrence(s))")
                    debug_lines_count += len(matches)

        clean_ratio = round(
            max(0.0, 1.0 - (debug_lines_count / max(1, total_added_lines))), 2
        )

        has_high_risk = any("breakpoint" in iss or "pdb" in iss for iss in issues)

        if has_high_risk:
            risk = "HIGH"
            ready = False
        elif issues:
            risk = "MEDIUM"
            ready = True
        else:
            risk = "LOW"
            ready = True

        report = PreflightAuditReport(
            is_sandbox_ready=ready,
            risk_level=risk,
            issues_detected=issues,
            clean_lines_ratio=clean_ratio,
        )

        logger.info(
            "preflight_patch_audit_complete",
            ready=ready,
            risk_level=risk,
            issues_count=len(issues),
            clean_ratio=clean_ratio,
        )

        return report
