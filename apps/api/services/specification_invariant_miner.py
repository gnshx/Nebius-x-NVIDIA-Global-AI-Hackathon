"""
RepoMedic — Specification Invariant Miner (VibeRepair 2026)

Inspired by:
- "VibeRepair: Behavior-Specification Automated Program Repair" (2026).
- NUS APR execution trace & specification discovery.

Addresses the critical APR failure mode where patches superficially silence errors
without enforcing explicit runtime preconditions or postcondition invariants:
1. Mines intended method preconditions (e.g. bounds, non-negativity, non-null guards).
2. Mines expected postconditions (return types, exception raising specifications).
3. Statically audits candidate diffs to ensure the inferred contract is explicitly guarded.
"""

from __future__ import annotations

import re
from typing import NamedTuple, List, Dict, Any, Optional


class SpecificationReport(NamedTuple):
    __test__ = False
    inferred_preconditions: List[str]
    inferred_postconditions: List[str]
    has_explicit_guard: bool
    contract_adherence_score: float
    violations: List[str]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inferred_preconditions": self.inferred_preconditions,
            "inferred_postconditions": self.inferred_postconditions,
            "has_explicit_guard": self.has_explicit_guard,
            "contract_adherence_score": round(self.contract_adherence_score, 3),
            "violations": self.violations,
            "recommendation": self.recommendation,
        }


class SpecificationInvariantMiner:
    """Mines and verifies behavioral preconditions & postcondition contracts."""

    # Common bug patterns triggering precondition requirements
    PRECONDITION_PATTERNS = [
        (re.compile(r"(?:negative|non-negative|< 0|ndigits|index|bound)", re.IGNORECASE), "Precondition: argument must be non-negative (>= 0)"),
        (re.compile(r"(?:null|none|empty string|missing value|missing key)", re.IGNORECASE), "Precondition: argument must be non-null / non-empty"),
        (re.compile(r"(?:typeerror|invalid type|expected (?:int|str|float|list|dict))", re.IGNORECASE), "Precondition: argument must conform to expected type signature"),
        (re.compile(r"(?:division by zero|zero division|denom|modulo by zero)", re.IGNORECASE), "Precondition: denominator must be non-zero"),
    ]

    # Explicit guard patterns in Python patch code
    GUARD_PATTERNS = [
        re.compile(r"if\s+[\w\.\(\)]+\s*(?:<|<=|==|!=|>|>=)\s*0:"),
        re.compile(r"if\s+[\w\.\(\)]+\s+is\s+None:"),
        re.compile(r"if\s+not\s+[\w\.\(\)]+:"),
        re.compile(r"if\s+[\w\.\(\)]+\s+is\s+not\s+None\s+and\s+[\w\.\(\)]+\s*<\s*0:"),
        re.compile(r"raise\s+(?:ValueError|TypeError|IndexError|KeyError)\("),
    ]

    def mine_specifications(self, issue_description: str, traceback_text: str = "") -> List[str]:
        """Infers intended runtime preconditions from issue text and traceback."""
        combined_text = f"{issue_description}\n{traceback_text}"
        specs: List[str] = []

        for pattern, spec_desc in self.PRECONDITION_PATTERNS:
            if pattern.search(combined_text):
                specs.append(spec_desc)

        if not specs:
            specs.append("Precondition: general input boundary validity")
        return specs

    def audit_patch_contract(
        self,
        diff_content: str,
        issue_description: str,
        traceback_text: str = "",
    ) -> SpecificationReport:
        """Audits whether a patch explicitly introduces the mined precondition guards."""
        specs = self.mine_specifications(issue_description, traceback_text)
        
        # Check if diff has added lines
        added_lines = [
            line[1:].strip() for line in diff_content.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        diff_text = "\n".join(added_lines)

        # Check for explicit defensive guards
        guards_found = [p for p in self.GUARD_PATTERNS if p.search(diff_text)]
        has_guard = len(guards_found) > 0

        # Check for expected postconditions (exception raising or valid return)
        postconditions: List[str] = []
        if "ValueError" in issue_description or "ValueError" in traceback_text:
            postconditions.append("Postcondition: raises ValueError on invalid input")
        elif "TypeError" in issue_description or "TypeError" in traceback_text:
            postconditions.append("Postcondition: raises TypeError on invalid type")
        else:
            postconditions.append("Postcondition: returns safe default or computed value")

        violations: List[str] = []
        # If precondition requires non-negative or non-null, but diff doesn't check it:
        is_negative_spec = any("non-negative" in s for s in specs)
        if is_negative_spec and not re.search(r"(?:<\s*0|non-negative|ValueError)", diff_text, re.IGNORECASE):
            violations.append("Contract Violation: Missing non-negative precondition check (< 0)")

        is_null_spec = any("non-null" in s for s in specs)
        if is_null_spec and not re.search(r"(?:is None|is not None|not \w+)", diff_text):
            violations.append("Contract Violation: Missing null/None boundary guard")

        # Compute adherence score
        if not violations and has_guard:
            score = 1.0
            rec = "Patch satisfies all mined behavioral contracts with explicit boundary guards."
        elif has_guard and violations:
            score = 0.65
            rec = f"Patch contains guards but misses specific contract assertions: {'; '.join(violations)}."
        elif not has_guard and not violations:
            score = 0.50
            rec = "Patch lacks explicit boundary validation guards (consider adding defensive check)."
        else:
            score = 0.20
            rec = f"Patch violates inferred runtime specification: {'; '.join(violations)}."

        return SpecificationReport(
            inferred_preconditions=specs,
            inferred_postconditions=postconditions,
            has_explicit_guard=has_guard,
            contract_adherence_score=score,
            violations=violations,
            recommendation=rec,
        )
