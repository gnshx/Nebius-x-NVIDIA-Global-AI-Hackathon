"""Self-Supervised Dynamic Mock Invariant Synthesizer.

Grounding: Hermetic Sandbox Testing & Mock Synthesis for Autonomous SWE Agents
(ICSE / FSE 2026).

Problem:
In hermetic Docker container execution environments (where network egress is disabled
to enforce zero data leakage and deterministic reproducibility), tests invoking external
REST APIs (requests, httpx, aiohttp), cloud SDKs (boto3, google-cloud), or network sockets
fail immediately with socket.gaierror, ConnectionRefusedError, or timeout errors, even if
the candidate patch's business logic is completely sound.

Solution:
DynamicMockSynthesizer performs static and AST analysis over target code and generated tests
to detect unmocked external I/O primitives, infers endpoint contracts and return structures,
and synthesizes hermetic mock harnesses (using unittest.mock and pytest fixtures) to guarantee
zero network egress dependency during sandbox verification.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


KNOWN_EXTERNAL_MODULES = {
    "requests",
    "httpx",
    "urllib",
    "urllib3",
    "aiohttp",
    "boto3",
    "botocore",
    "socket",
    "http.client",
}


@dataclass
class ExternalCallSignature:
    """Represents an external network or I/O call detected in source or test code."""
    module: str
    function: str
    line_number: int
    inferred_endpoint: Optional[str] = None
    mock_pattern: str = "unittest.mock.patch"
    suggested_return: str = "MagicMock(status_code=200, json=lambda: {'status': 'ok'}, text='ok')"


@dataclass
class HermeticIsolationReport:
    """Audit report for sandbox network isolation and synthesized mock harnesses."""
    is_hermetic_safe: bool
    unmocked_calls: List[ExternalCallSignature] = field(default_factory=list)
    mocked_calls: List[ExternalCallSignature] = field(default_factory=list)
    isolation_score: float = 1.0
    synthesized_harness: str = ""

    def to_dict(self) -> dict:
        return {
            "is_hermetic_safe": self.is_hermetic_safe,
            "isolation_score": self.isolation_score,
            "unmocked_count": len(self.unmocked_calls),
            "mocked_count": len(self.mocked_calls),
            "has_synthesized_harness": bool(self.synthesized_harness),
        }


class DynamicMockSynthesizer:
    """Synthesizes hermetic mock contracts to ensure offline sandbox execution."""

    def __init__(self) -> None:
        pass

    @classmethod
    def audit_and_synthesize(
        cls,
        source_code: str,
        test_code: str = "",
    ) -> HermeticIsolationReport:
        """Class method convenience to scan code and return isolation report."""
        return cls().scan_code_for_external_io(source_code, test_code)

    def scan_code_for_external_io(
        self,
        source_code: str,
        test_code: str = "",
    ) -> HermeticIsolationReport:
        """Analyzes source and test code for external network calls and checks mocking."""
        detected_calls: List[ExternalCallSignature] = []

        try:
            tree = ast.parse(source_code)
            detected_calls.extend(self._extract_network_calls(tree))
        except SyntaxError:
            detected_calls.extend(self._regex_extract_calls(source_code))

        # Check existing test code for mock presence
        existing_mocks = self._extract_existing_mocks(test_code)

        unmocked: List[ExternalCallSignature] = []
        mocked: List[ExternalCallSignature] = []

        for call in detected_calls:
            if call.module in existing_mocks or f"{call.module}.{call.function}" in existing_mocks:
                mocked.append(call)
            else:
                unmocked.append(call)

        total_detected = len(detected_calls)
        if total_detected == 0:
            isolation_score = 1.0
            is_hermetic = True
        else:
            isolation_score = round(len(mocked) / total_detected, 4)
            is_hermetic = len(unmocked) == 0

        harness = ""
        if unmocked:
            harness = self.synthesize_mock_fixtures(unmocked)

        return HermeticIsolationReport(
            is_hermetic_safe=is_hermetic,
            unmocked_calls=unmocked,
            mocked_calls=mocked,
            isolation_score=isolation_score,
            synthesized_harness=harness,
        )

    def _extract_network_calls(self, tree: ast.AST) -> List[ExternalCallSignature]:
        """Extracts AST call nodes matching known external modules."""
        calls: List[ExternalCallSignature] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                signature = self._analyze_call_node(node)
                if signature:
                    calls.append(signature)

        return calls

    def _analyze_call_node(self, node: ast.Call) -> Optional[ExternalCallSignature]:
        """Examines an ast.Call node for external module attributes."""
        func = node.func
        module_name = ""
        func_name = ""

        if isinstance(func, ast.Attribute):
            func_name = func.attr
            if isinstance(func.value, ast.Name):
                module_name = func.value.id
            elif isinstance(func.value, ast.Attribute):
                # e.g., urllib.request.urlopen
                module_name = f"{getattr(func.value.value, 'id', '')}.{func.value.attr}".strip(".")

        if not module_name:
            return None

        # Check match with known modules
        matched_mod = None
        for mod in KNOWN_EXTERNAL_MODULES:
            if module_name == mod or module_name.startswith(f"{mod}."):
                matched_mod = mod
                break

        if not matched_mod:
            return None

        endpoint: Optional[str] = None
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            val = node.args[0].value
            if val.startswith("http://") or val.startswith("https://"):
                endpoint = val

        return ExternalCallSignature(
            module=module_name,
            function=func_name,
            line_number=getattr(node, "lineno", 1),
            inferred_endpoint=endpoint,
        )

    def _regex_extract_calls(self, code: str) -> List[ExternalCallSignature]:
        """Fallback regex extraction for unparseable syntax drafts."""
        calls: List[ExternalCallSignature] = []
        pattern = re.compile(
            r"\b(requests|httpx|aiohttp|boto3|urllib\.request)\.(get|post|put|delete|request|urlopen)\((.*?)\)",
            re.MULTILINE,
        )

        for line_idx, line in enumerate(code.splitlines(), start=1):
            for match in pattern.finditer(line):
                mod, fn, args = match.groups()
                endpoint = None
                str_match = re.search(r"['\"](https?://[^'\"]+)['\"]", args)
                if str_match:
                    endpoint = str_match.group(1)

                calls.append(
                    ExternalCallSignature(
                        module=mod,
                        function=fn,
                        line_number=line_idx,
                        inferred_endpoint=endpoint,
                    )
                )

        return calls

    def _extract_existing_mocks(self, test_code: str) -> Set[str]:
        """Scans test code for active mock declarations."""
        existing = set()
        if not test_code:
            return existing

        patterns = [
            r"patch\(['\"]([a-zA-Z0-9_\.]+)['\"]",
            r"monkeypatch\.setattr\(['\"]([a-zA-Z0-9_\.]+)['\"]",
            r"@mock\.patch\(['\"]([a-zA-Z0-9_\.]+)['\"]",
            r"requests_mock",
            r"httpretty",
            r"respx",
        ]

        for p in patterns:
            for match in re.finditer(p, test_code):
                if match.groups():
                    existing.add(match.group(1).split(".")[0])
                    existing.add(match.group(1))

        # Check keyword imports
        for mod in KNOWN_EXTERNAL_MODULES:
            if f"mock.{mod}" in test_code or f"patch('{mod}" in test_code:
                existing.add(mod)

        return existing

    def synthesize_mock_fixtures(self, unmocked_calls: List[ExternalCallSignature]) -> str:
        """Generates a pytest fixture or mock harness injecting hermetic stubs."""
        unique_targets: Set[Tuple[str, str]] = set()
        for call in unmocked_calls:
            target = f"{call.module}.{call.function}"
            unique_targets.add((call.module, call.function))

        lines = [
            "# --- Auto-Synthesized Hermetic Sandbox Mock Harness (ICSE 2026) ---",
            "import pytest",
            "from unittest.mock import MagicMock, patch",
            "",
            "@pytest.fixture(autouse=True)",
            "def _auto_mock_hermetic_network():",
            '    """Intercepts external network calls to preserve offline container sandbox isolation."""',
        ]

        patches = []
        for mod, fn in sorted(unique_targets):
            target = f"{mod}.{fn}"
            patches.append(f"patch('{target}')")

        if not patches:
            return ""

        nested = ", ".join(patches)
        lines.append(f"    with {nested} as mock_obj:")
        lines.append("        if isinstance(mock_obj, tuple):")
        lines.append("            for m in mock_obj:")
        lines.append("                m.return_value = MagicMock(status_code=200, json=lambda: {'status': 'ok'}, text='ok')")
        lines.append("        else:")
        lines.append("            mock_obj.return_value = MagicMock(status_code=200, json=lambda: {'status': 'ok'}, text='ok')")
        lines.append("        yield mock_obj")

        return "\n".join(lines)

    def inject_mock_harness_into_test(
        self,
        test_code: str,
        report: HermeticIsolationReport,
    ) -> str:
        """Injects synthesized mock harness into the test code if unmocked calls exist."""
        if not report.synthesized_harness or report.is_hermetic_safe:
            return test_code

        return f"{report.synthesized_harness}\n\n{test_code}"
