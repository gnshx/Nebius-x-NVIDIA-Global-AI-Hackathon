"""Differential Resource Finalization Auditor.

Grounding: Amur: Resource Flow Analysis for Automated Program Repair (ASE 2025)
& Resource Invariant Preservation in Automated Program Repair (ICSE 2026).

Problem:
LLM-generated repair patches frequently introduce silent resource leaks: opening files
(open()), database connections (sqlite3.connect, sessionmaker), sockets, or mutex locks
without enclosing with-statements or try-finally cleanup. While micro unit tests pass,
these patches cause production resource exhaustion (Errno 24: Too many open files).

Solution:
DifferentialResourceFinalizationAuditor statically analyzes AST scopes in candidate patches
to ensure all acquired I/O and synchronization resources are deterministically finalized.
It computes a Resource Safety Score (0.0 to 1.0) and automatically suggests or applies
canonical context-manager transformations (e.g. converting bare open() into with open()).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


RESOURCE_CREATION_FUNCTIONS = {
    "open": "file_handle",
    "socket.socket": "socket",
    "socket.create_connection": "socket",
    "sqlite3.connect": "database_connection",
    "psycopg2.connect": "database_connection",
    "asyncpg.connect": "database_connection",
    "SessionLocal": "database_session",
    "threading.Lock": "mutex_lock",
}


@dataclass
class LeakHazard:
    """Represents a potential resource allocation hazard detected in patch code."""
    resource_type: str
    target_call: str
    line_number: int
    assigned_var: Optional[str] = None
    is_safely_finalized: bool = False
    remediation_suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "resource_type": self.resource_type,
            "target_call": self.target_call,
            "line_number": self.line_number,
            "assigned_var": self.assigned_var,
            "is_safely_finalized": self.is_safely_finalized,
            "remediation_suggestion": self.remediation_suggestion,
        }


@dataclass
class ResourceAuditReport:
    """Audit report detailing resource allocation and deterministic finalization."""
    has_leaks: bool
    safety_score: float
    hazards: List[LeakHazard] = field(default_factory=list)
    unfinalized_count: int = 0
    remediated_code: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "has_leaks": self.has_leaks,
            "safety_score": self.safety_score,
            "unfinalized_count": self.unfinalized_count,
            "total_hazards": len(self.hazards),
            "hazards": [h.to_dict() for h in self.hazards],
        }


class DifferentialResourceFinalizationAuditor:
    """Audits patch code to ensure deterministic resource finalization and leak prevention."""

    def __init__(self) -> None:
        pass

    @classmethod
    def audit_code(cls, source_code: str) -> ResourceAuditReport:
        """Class method convenience to audit code string for resource finalization."""
        return cls().audit(source_code)

    def audit(self, source_code: str) -> ResourceAuditReport:
        """Audits source code or diff addition lines for unclosed I/O resources."""
        if not source_code.strip():
            return ResourceAuditReport(has_leaks=False, safety_score=1.0, hazards=[], unfinalized_count=0)

        try:
            tree = ast.parse(source_code)
            hazards = self._analyze_ast_resources(tree)
        except SyntaxError:
            hazards = self._regex_fallback_audit(source_code)

        unfinalized = [h for h in hazards if not h.is_safely_finalized]
        total = len(hazards)
        if total == 0:
            score = 1.0
            has_leaks = False
        else:
            score = round((total - len(unfinalized)) / total, 4)
            has_leaks = len(unfinalized) > 0

        remediated: Optional[str] = None
        if has_leaks:
            remediated = self._auto_remediate_bare_opens(source_code, unfinalized)

        return ResourceAuditReport(
            has_leaks=has_leaks,
            safety_score=score,
            hazards=hazards,
            unfinalized_count=len(unfinalized),
            remediated_code=remediated,
        )

    def _analyze_ast_resources(self, tree: ast.AST) -> List[LeakHazard]:
        """Traverses AST to detect resource allocations and check if enclosed in with/finally."""
        hazards: List[LeakHazard] = []

        # Track with-statement items to know which calls are safely context-managed
        with_items: Set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if hasattr(item.context_expr, "lineno"):
                        with_items.add(item.context_expr.lineno)

        # Check all function calls in AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._resolve_call_name(node.func)
                matched_type = self._match_resource_type(call_name)
                if matched_type:
                    lineno = getattr(node, "lineno", 1)
                    is_with_managed = lineno in with_items

                    # Check parent assignment if any
                    assigned_var = None
                    is_closed = False

                    if not is_with_managed:
                        assigned_var = self._find_assigned_variable(tree, lineno)
                        if assigned_var:
                            is_closed = self._has_corresponding_close(tree, assigned_var, lineno)

                    is_safe = is_with_managed or is_closed
                    suggestion = ""
                    if not is_safe:
                        suggestion = f"Wrap '{call_name}()' in a 'with' context manager or invoke '.close()' in a finally block."

                    hazards.append(
                        LeakHazard(
                            resource_type=matched_type,
                            target_call=call_name,
                            line_number=lineno,
                            assigned_var=assigned_var,
                            is_safely_finalized=is_safe,
                            remediation_suggestion=suggestion,
                        )
                    )

        return hazards

    def _resolve_call_name(self, node: ast.AST) -> str:
        """Resolves dotted or simple call function name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._resolve_call_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        return ""

    def _match_resource_type(self, call_name: str) -> Optional[str]:
        """Matches function call against known resource creators."""
        for target, res_type in RESOURCE_CREATION_FUNCTIONS.items():
            if call_name == target or call_name.endswith(f".{target}"):
                return res_type
        return None

    def _find_assigned_variable(self, tree: ast.AST, call_line: int) -> Optional[str]:
        """Finds if a resource call at call_line is assigned to a variable name."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and getattr(node, "lineno", 0) == call_line:
                if node.targets and isinstance(node.targets[0], ast.Name):
                    return node.targets[0].id
        return None

    def _has_corresponding_close(self, tree: ast.AST, var_name: str, after_line: int) -> bool:
        """Checks if var_name.close() or release() is invoked downstream."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node, "lineno", 0) > after_line:
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("close", "release", "dispose"):
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == var_name:
                            return True
        return False

    def _regex_fallback_audit(self, source_code: str) -> List[LeakHazard]:
        """Fallback regex analysis for draft fragments."""
        hazards = []
        pattern = re.compile(r"(\b[a-zA-Z_0-9]+)\s*=\s*(open|sqlite3\.connect|socket\.socket)\((.*?)\)")
        for idx, line in enumerate(source_code.splitlines(), start=1):
            if "with " in line:
                continue
            match = pattern.search(line)
            if match:
                var, fn, _ = match.groups()
                hazards.append(
                    LeakHazard(
                        resource_type=self._match_resource_type(fn) or "resource",
                        target_call=fn,
                        line_number=idx,
                        assigned_var=var,
                        is_safely_finalized=False,
                        remediation_suggestion=f"Convert to 'with {fn}(...) as {var}:'",
                    )
                )
        return hazards

    def _auto_remediate_bare_opens(self, source_code: str, unfinalized: List[LeakHazard]) -> str:
        """Provides automatic safe context-manager transformation for bare open() calls."""
        lines = source_code.splitlines()
        for h in unfinalized:
            if h.target_call == "open" and h.assigned_var and 1 <= h.line_number <= len(lines):
                target_line = lines[h.line_number - 1]
                # Match e.g. "f = open('file.txt', 'r')"
                bare_match = re.search(r"(\s*)" + re.escape(h.assigned_var) + r"\s*=\s*open\((.*?)\)", target_line)
                if bare_match:
                    indent, args = bare_match.groups()
                    lines[h.line_number - 1] = f"{indent}with open({args}) as {h.assigned_var}:"
        return "\n".join(lines)
