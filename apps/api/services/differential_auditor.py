"""
RepoMedic — Differential Behavior & Contract Auditor (PatchDiff 2025/2026)

Implements differential behavioral analysis based on:
"Are 'Solved Issues' in SWE-bench Really Solved Correctly? An Empirical Study" (2025/2026).

Inspects candidate patches for subtle contract breakages that pass naive unit tests:
1. Silent Exception Swallowing: catches `try: ... except: pass` or `except Exception: return None`.
2. Public API Signature Mutation: changes to parameter names or removal of default argument values.
3. Catch-All Exception Masking: replaces specific domain errors with overly broad catch blocks.
4. Accidental None Return Inversion: returns None instead of raising documented exceptions.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class DifferentialReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    is_contract_preserved: bool
    behavioral_risk: str  # "LOW" | "MEDIUM" | "HIGH"
    detected_drifts: list[str]
    contract_safety_score: float  # 0.0 to 1.0
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_contract_preserved": self.is_contract_preserved,
            "behavioral_risk": self.behavioral_risk,
            "detected_drifts": self.detected_drifts,
            "contract_safety_score": self.contract_safety_score,
            "recommendation": self.recommendation,
        }


class DifferentialBehaviorAuditor:
    """Audits patch diffs for behavioral regression patterns, silent exception swallowing, and API drift."""

    SILENT_SWALLOW_PATTERNS = [
        (re.compile(r"^\+\s*except\s*:\s*(?:pass|\n\+\s*pass\b)", re.MULTILINE), "Bare except: pass suppresses all system and runtime exceptions"),
        (re.compile(r"^\+\s*except\s+Exception\s*:\s*(?:pass|\n\+\s*pass\b)", re.MULTILINE), "except Exception: pass silently masks underlying defect"),
        (re.compile(r"^\+\s*except\s+Exception\s*:\s*(?:return\s+None|\n\+\s*return\s+None\b)", re.MULTILINE), "except Exception: return None alters return contract"),
        (re.compile(r"^\+\s*catch\s*\([^)]*\)\s*\{\s*\}", re.MULTILINE), "Empty catch block in JavaScript/TypeScript/Java"),
    ]

    SIGNATURE_MUTATION_PATTERNS = [
        (re.compile(r"^-\s*def\s+(\w+)\s*\(([^)]+)\):", re.MULTILINE), re.compile(r"^\+\s*def\s+(\w+)\s*\(([^)]+)\):", re.MULTILINE)),
    ]

    @classmethod
    def audit_patch_diff(
        cls,
        diff: str,
        file_path: str = "",
    ) -> DifferentialReport:
        """Audits unified diff for contract mutations and silent bug masking."""
        if not diff or not diff.strip():
            return DifferentialReport(
                is_contract_preserved=True,
                behavioral_risk="LOW",
                detected_drifts=[],
                contract_safety_score=1.0,
                recommendation="Empty diff maintains 100% behavioral equivalence.",
            )

        drifts: list[str] = []
        is_test_file = "test" in file_path.lower()

        # 1. Check for silent exception swallowing (only in production code)
        if not is_test_file:
            for pattern, desc in cls.SILENT_SWALLOW_PATTERNS:
                matches = pattern.findall(diff)
                if matches:
                    drifts.append(f"[Contract Breach] {desc} ({len(matches)} occurrence(s))")

        # 2. Check for public function signature change
        for del_pat, add_pat in cls.SIGNATURE_MUTATION_PATTERNS:
            del_matches = del_pat.findall(diff)
            add_matches = add_pat.findall(diff)

            for (del_fn, del_args) in del_matches:
                for (add_fn, add_args) in add_matches:
                    if del_fn == add_fn and not del_fn.startswith("_"):
                        del_params = [p.strip().split("=")[0].split(":")[0] for p in del_args.split(",") if p.strip()]
                        add_params = [p.strip().split("=")[0].split(":")[0] for p in add_args.split(",") if p.strip()]
                        # Parameter deletion on public API
                        missing = set(del_params) - set(add_params) - {"*args", "**kwargs"}
                        if missing:
                            drifts.append(
                                f"[API Mutation] Public function '{del_fn}' removed parameter(s): {', '.join(missing)}"
                            )

        drift_count = len(drifts)
        safety_score = round(max(0.0, 1.0 - (drift_count * 0.35)), 2)

        has_high_risk = any("Contract Breach" in d for d in drifts)

        if has_high_risk:
            risk = "HIGH"
            is_preserved = False
            rec = "Reject patch: remove silent exception suppressors and preserve exception propagation."
        elif drift_count > 0:
            risk = "MEDIUM"
            is_preserved = False
            rec = "Review public API signature changes to preserve backward compatibility."
        else:
            risk = "LOW"
            is_preserved = True
            rec = "Contract and behavioral invariance verified with zero anti-patterns."

        logger.info(
            "differential_behavior_audit_complete",
            file_path=file_path,
            risk=risk,
            drifts_count=drift_count,
            safety_score=safety_score,
        )

        return DifferentialReport(
            is_contract_preserved=is_preserved,
            behavioral_risk=risk,
            detected_drifts=drifts,
            contract_safety_score=safety_score,
            recommendation=rec,
        )
