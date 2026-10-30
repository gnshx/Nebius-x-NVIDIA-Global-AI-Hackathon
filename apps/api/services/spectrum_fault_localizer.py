"""
RepoMedic — Spectrum-Based Fault Localizer (SBFL - AutoCodeRover / LLM4FL 2026)

Inspired by:
- "AutoCodeRover: Autonomous Program Improvement with Spectrum-Based Fault Localization" (2024–2026).
- "LLM4FL: Multi-Agent Software Fault Localization" (2025/2026).

Addresses the critical SWE-bench failure mode where purely semantic vector search
dilutes attention by retrieving textually related but non-executing code.
Uses mathematical suspiciousness coefficients:
1. Ochiai formula:
   Ochiai(e) = failed(e) / sqrt(total_failed * (failed(e) + passed(e)))
2. DStar (D*) formula:
   D*(e) = (failed(e))^2 / (passed(e) + (total_failed - failed(e)))
"""

from __future__ import annotations

import math
import re
from typing import NamedTuple, List, Dict, Any, Optional


class SuspiciousLocation(NamedTuple):
    __test__ = False
    file_path: str
    function_name: str
    line_number: int
    ochiai_score: float
    dstar_score: float
    failed_count: int
    passed_count: int
    is_primary_culprit: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "function_name": self.function_name,
            "line_number": self.line_number,
            "ochiai_score": round(self.ochiai_score, 4),
            "dstar_score": round(self.dstar_score, 4),
            "failed_count": self.failed_count,
            "passed_count": self.passed_count,
            "is_primary_culprit": self.is_primary_culprit,
        }


class SpectrumFaultLocalizer:
    """Computes Ochiai and DStar suspiciousness scores across repository locations."""

    @staticmethod
    def calculate_ochiai(failed_e: int, passed_e: int, total_failed: int) -> float:
        """Computes the statistical Ochiai suspiciousness coefficient."""
        if total_failed == 0 or (failed_e + passed_e) == 0:
            return 0.0
        denominator = math.sqrt(total_failed * (failed_e + passed_e))
        return failed_e / denominator if denominator > 0 else 0.0

    @staticmethod
    def calculate_dstar(failed_e: int, passed_e: int, total_failed: int, star_power: int = 2) -> float:
        """Computes the DStar (D*) suspiciousness score."""
        numerator = failed_e ** star_power
        denominator = passed_e + (total_failed - failed_e)
        if denominator == 0:
            return float(numerator) if numerator > 0 else 0.0
        return numerator / denominator

    @classmethod
    def localize_from_tracebacks(
        cls,
        failing_tracebacks: List[str],
        total_failed_tests: int,
        passing_locations: Optional[Dict[str, int]] = None,
    ) -> List[SuspiciousLocation]:
        """Parses traceback stacks and computes suspiciousness rankings for each frame."""
        if not failing_tracebacks or total_failed_tests <= 0:
            return []

        passing_map = passing_locations or {}
        # Count failures per location: key = (file, func, line)
        location_fail_counts: Dict[tuple[str, str, int], int] = {}

        traceback_pattern = re.compile(
            r'File\s+["\']([^"\']+)["\'],\s+line\s+(\d+),\s+in\s+([a-zA-Z0-9_<>\.]+)'
        )

        for tb in failing_tracebacks:
            seen_in_tb = set()
            for match in traceback_pattern.finditer(tb):
                file_path = match.group(1).replace("\\", "/")
                line_no = int(match.group(2))
                func_name = match.group(3)

                # Skip standard library and site-packages
                if any(p in file_path for p in ["/lib/python", "/site-packages/", "<string>", "<frozen"]):
                    continue

                loc_key = (file_path, func_name, line_no)
                if loc_key not in seen_in_tb:
                    seen_in_tb.add(loc_key)
                    location_fail_counts[loc_key] = location_fail_counts.get(loc_key, 0) + 1

        results: List[SuspiciousLocation] = []
        for (f_path, f_name, l_num), fail_count in location_fail_counts.items():
            key_str = f"{f_path}:{f_name}"
            pass_count = passing_map.get(key_str, 0)

            ochiai = cls.calculate_ochiai(fail_count, pass_count, total_failed_tests)
            dstar = cls.calculate_dstar(fail_count, pass_count, total_failed_tests)

            results.append(
                SuspiciousLocation(
                    file_path=f_path,
                    function_name=f_name,
                    line_number=l_num,
                    ochiai_score=ochiai,
                    dstar_score=dstar,
                    failed_count=fail_count,
                    passed_count=pass_count,
                    is_primary_culprit=False,
                )
            )

        # Sort descending by Ochiai then DStar
        results.sort(key=lambda x: (x.ochiai_score, x.dstar_score), reverse=True)

        if results:
            # Mark the top result as primary culprit
            top = results[0]
            results[0] = top._replace(is_primary_culprit=True)

        return results
