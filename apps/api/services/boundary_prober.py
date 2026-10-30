"""
RepoMedic — Boundary Condition Prober & Edge-Case Synthesizer

Implements behavioral property probing from:
- PROBE: Behavioral Probing & Invariant Consensus in Automated Program Repair (2026)
- Systematic Boundary Condition Testing for Robust APR (2025/2026)

Generates targeted boundary condition inputs (negative values, None, zero, empty containers)
to verify that synthesized bug fixes do not fail on adjacent input boundaries (e.g. humanize #466).
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple
import structlog

logger = structlog.get_logger(__name__)


class BoundaryProbe(NamedTuple):
    __test__ = False
    parameter_name: str
    edge_value_repr: str
    rationale: str
    expected_behavior: str  # "RAISE_VALUE_ERROR" | "HANDLE_GRACEFULLY" | "RETURN_DEFAULT"
    suggested_code: str


class BoundaryProbingResult(NamedTuple):
    __test__ = False
    function_name: str
    probes: list[BoundaryProbe]
    total_probes: int
    edge_coverage_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "function_name": self.function_name,
            "probes": [
                {
                    "parameter_name": p.parameter_name,
                    "edge_value_repr": p.edge_value_repr,
                    "rationale": p.rationale,
                    "expected_behavior": p.expected_behavior,
                    "suggested_code": p.suggested_code,
                }
                for p in self.probes
            ],
            "total_probes": self.total_probes,
            "edge_coverage_score": self.edge_coverage_score,
        }


class BoundaryProber:
    """Infers boundary edge cases from function signatures and code context."""

    PARAM_PATTERN = re.compile(r"def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)", re.MULTILINE)

    # Keywords suggesting numeric constraints
    NUMERIC_KEYWORDS = {"digits", "ndigits", "limit", "offset", "count", "width", "prec", "precision", "size", "idx", "index"}
    # Keywords suggesting string inputs
    STRING_KEYWORDS = {"text", "string", "name", "val", "value", "fmt", "format", "pattern"}
    # Keywords suggesting container inputs
    CONTAINER_KEYWORDS = {"items", "list", "array", "data", "elements", "mapping", "config"}

    @classmethod
    def probe_function(
        cls,
        func_code: str,
        target_function: str | None = None,
    ) -> BoundaryProbingResult:
        """
        Analyzes a function definition and synthesizes boundary condition probes.
        """
        matches = cls.PARAM_PATTERN.findall(func_code)
        if not matches:
            return BoundaryProbingResult(
                function_name=target_function or "unknown",
                probes=[],
                total_probes=0,
                edge_coverage_score=0.0,
            )

        # Match target function if specified, otherwise take first definition
        selected_func = matches[0][0]
        params_str = matches[0][1]

        if target_function:
            for fname, pstr in matches:
                if fname.lower() == target_function.lower():
                    selected_func = fname
                    params_str = pstr
                    break

        # Parse parameter names
        params = [p.split("=")[0].split(":")[0].strip() for p in params_str.split(",") if p.strip()]
        params = [p for p in params if p not in ("self", "cls", "*args", "**kwargs")]

        probes: list[BoundaryProbe] = []

        for p in params:
            p_lower = p.lower()

            # 1. Nullability probe for all non-self parameters
            probes.append(
                BoundaryProbe(
                    parameter_name=p,
                    edge_value_repr="None",
                    rationale=f"Verify parameter '{p}' handles None without unhandled TypeError/AttributeError",
                    expected_behavior="HANDLE_GRACEFULLY",
                    suggested_code=f"assert {selected_func}(..., {p}=None) is not None",
                )
            )

            # 2. Numeric boundary probes (negative, zero, extreme)
            if any(k in p_lower for k in cls.NUMERIC_KEYWORDS):
                probes.append(
                    BoundaryProbe(
                        parameter_name=p,
                        edge_value_repr="-1",
                        rationale=f"Negative boundary for numeric parameter '{p}'",
                        expected_behavior="RAISE_VALUE_ERROR",
                        suggested_code=f"with pytest.raises(ValueError):\n    {selected_func}(..., {p}=-1)",
                    )
                )
                probes.append(
                    BoundaryProbe(
                        parameter_name=p,
                        edge_value_repr="0",
                        rationale=f"Zero boundary for numeric parameter '{p}'",
                        expected_behavior="HANDLE_GRACEFULLY",
                        suggested_code=f"{selected_func}(..., {p}=0)",
                    )
                )

            # 3. String boundary probes
            if any(k in p_lower for k in cls.STRING_KEYWORDS):
                probes.append(
                    BoundaryProbe(
                        parameter_name=p,
                        edge_value_repr='""',
                        rationale=f"Empty string boundary for '{p}'",
                        expected_behavior="HANDLE_GRACEFULLY",
                        suggested_code=f"{selected_func}(..., {p}='')",
                    )
                )

            # 4. Container boundary probes
            if any(k in p_lower for k in cls.CONTAINER_KEYWORDS):
                probes.append(
                    BoundaryProbe(
                        parameter_name=p,
                        edge_value_repr="[]",
                        rationale=f"Empty container boundary for '{p}'",
                        expected_behavior="HANDLE_GRACEFULLY",
                        suggested_code=f"{selected_func}(..., {p}=[])",
                    )
                )

        coverage_score = round(min(1.0, 0.4 + (0.15 * len(probes))), 2)

        logger.info(
            "boundary_probing_complete",
            func=selected_func,
            params_count=len(params),
            probes_count=len(probes),
            coverage_score=coverage_score,
        )

        return BoundaryProbingResult(
            function_name=selected_func,
            probes=probes,
            total_probes=len(probes),
            edge_coverage_score=coverage_score,
        )
