"""
RepoMedic — Static AST Linter & NameError Validator (SWE-bench 2026)

Addresses the frequent SWE-bench failure mode where LLM-generated patches
reference undefined variables or omitted imports (triggering NameError),
wasting costly container sandbox executions.

Statically analyzes Python code blocks via AST NodeVisitor:
1. Tracks assigned names, function args, and imported symbols.
2. Identifies references to undefined identifiers before sandbox execution.
3. Distinguishes built-ins, standard library, and module globals.
"""

from __future__ import annotations

import ast
import builtins
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)

STANDARD_BUILTINS = set(dir(builtins)) | {
    "__file__", "__name__", "__doc__", "__package__", "self", "cls"
}


class LinterReport(NamedTuple):
    __test__ = False  # Prevent pytest collection

    is_clean: bool
    undefined_names: list[str]
    has_syntax_errors: bool
    warning_count: int
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_clean": self.is_clean,
            "undefined_names": self.undefined_names,
            "has_syntax_errors": self.has_syntax_errors,
            "warning_count": self.warning_count,
            "details": self.details,
        }


class _ScopeSymbolCollector(ast.NodeVisitor):
    """Collects defined and referenced symbols within a Python AST module or function."""

    def __init__(self, external_scope_symbols: set[str] | None = None) -> None:
        self.defined_symbols: set[str] = set(STANDARD_BUILTINS)
        if external_scope_symbols:
            self.defined_symbols.update(external_scope_symbols)
        self.loaded_names: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.defined_symbols.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.defined_symbols.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_symbols.add(node.name)
        # Register function arguments
        for arg in node.args.args:
            self.defined_symbols.add(arg.arg)
        for arg in node.args.posonlyargs:
            self.defined_symbols.add(arg.arg)
        for arg in node.args.kwonlyargs:
            self.defined_symbols.add(arg.arg)
        if node.args.vararg:
            self.defined_symbols.add(node.args.vararg.arg)
        if node.args.kwarg:
            self.defined_symbols.add(node.args.kwarg.arg)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_symbols.add(node.name)
        for arg in node.args.args:
            self.defined_symbols.add(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined_symbols.add(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.defined_symbols.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.loaded_names.add(node.id)
        self.generic_visit(node)


class StaticLinterValidator:
    """Validates Python code and patches against common static defects (e.g. NameError)."""

    @classmethod
    def validate_code(
        cls,
        code: str,
        known_globals: set[str] | None = None,
    ) -> LinterReport:
        """Statically inspects Python code for undefined variables and syntax integrity."""
        if not code.strip():
            return LinterReport(
                is_clean=True,
                undefined_names=[],
                has_syntax_errors=False,
                warning_count=0,
                details="Empty code buffer is clean.",
            )

        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            return LinterReport(
                is_clean=False,
                undefined_names=[],
                has_syntax_errors=True,
                warning_count=1,
                details=f"SyntaxError on line {se.lineno}: {se.msg}",
            )

        collector = _ScopeSymbolCollector(external_scope_symbols=known_globals)
        collector.visit(tree)

        undefined = sorted(list(collector.loaded_names - collector.defined_symbols))

        is_clean = len(undefined) == 0
        details = (
            "Static AST linter passed with 0 undefined symbols."
            if is_clean
            else f"Detected {len(undefined)} undefined symbol(s): {', '.join(undefined[:5])}"
        )

        return LinterReport(
            is_clean=is_clean,
            undefined_names=undefined,
            has_syntax_errors=False,
            warning_count=len(undefined),
            details=details,
        )
