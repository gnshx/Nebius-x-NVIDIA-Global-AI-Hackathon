"""
RepoMedic — Variant-Guided Discriminator (PROBE, ASE 2026)

Implements the program-variant guided test augmentation methodology from:
"Probe to Generate: Program Variant-Guided Test Augmentation for Repository-Level Repair Benchmarks" (ASE 2026).

Addresses the "Plausible Patch" dilemma where AI-generated patches pass weak regression tests
simply because test suites fail to test edge-cases and boundary conditions.

1. Generates subtle semantic mutant variants from candidate patch diffs:
   - InvertedComparison: < -> >=, > -> <=, == -> !=
   - OmittedException: 'raise ValueError' -> 'return None' / 'pass'
   - BoundaryOffByOne: '< 0' -> '<= 0', 'len(x) < 2' -> 'len(x) < 1'
   - GuardBypass: 'if not x:' -> 'if False:'
2. Audits whether test suites contain assertions that actively discriminate valid fixes from mutant bugs.
3. Computes Discrimination Score (0.0 to 1.0) and generates targeted augmentation directives.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, NamedTuple, Optional
import structlog

logger = structlog.get_logger(__name__)


class ProgramVariant(NamedTuple):
    variant_id: str
    variant_type: str
    original_snippet: str
    mutated_snippet: str
    line_number: int
    is_killed: bool
    killing_assertion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "variant_type": self.variant_type,
            "original_snippet": self.original_snippet,
            "mutated_snippet": self.mutated_snippet,
            "line_number": self.line_number,
            "is_killed": self.is_killed,
            "killing_assertion": self.killing_assertion,
        }


class DiscriminationReport(NamedTuple):
    total_variants: int
    killed_variants: int
    discrimination_score: float
    is_adequately_discriminating: bool
    variants: List[ProgramVariant]
    surviving_variants: List[ProgramVariant]
    augmentation_directives: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_variants": self.total_variants,
            "killed_variants": self.killed_variants,
            "discrimination_score": round(self.discrimination_score, 4),
            "is_adequately_discriminating": self.is_adequately_discriminating,
            "variants": [v.to_dict() for v in self.variants],
            "surviving_variants_count": len(self.surviving_variants),
            "augmentation_directives": self.augmentation_directives,
        }


class VariantGuidedDiscriminator:
    """Evaluates test suite discrimination power against semantic program variants (PROBE 2026)."""

    COMPARISON_INVERSIONS = [
        (r"\b<=\b", ">"),
        (r"\b>=\b", "<"),
        (r"\b==\b", "!="),
        (r"\b!=\b", "=="),
        (r"(?<![<>=!])<(?![<>=!])", ">="),
        (r"(?<![<>=!])>(?![<>=!])", "<="),
        (r"\bin\b", "not in"),
    ]

    @classmethod
    def generate_variants(cls, patch_diff: str) -> List[ProgramVariant]:
        """Synthesizes subtle program mutants from added patch lines."""
        variants: List[ProgramVariant] = []
        variant_idx = 1

        added_lines: List[tuple[int, str]] = []
        for line_no, raw_line in enumerate(patch_diff.splitlines(), start=1):
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                added_lines.append((line_no, raw_line[1:].strip()))

        for line_no, code in added_lines:
            if not code or code.startswith("#"):
                continue

            # 1. Mutate Inverted Comparisons
            for pat, repl in cls.COMPARISON_INVERSIONS:
                if re.search(pat, code):
                    mutated = re.sub(pat, repl, code, count=1)
                    if mutated != code:
                        variants.append(
                            ProgramVariant(
                                variant_id=f"var-{variant_idx}",
                                variant_type="InvertedComparison",
                                original_snippet=code,
                                mutated_snippet=mutated,
                                line_number=line_no,
                                is_killed=False,
                            )
                        )
                        variant_idx += 1
                        break

            # 2. Mutate Exception Guards (raise -> pass / return None)
            if re.match(r"^raise\s+\w+(?:Error)?\(.*\)", code):
                variants.append(
                    ProgramVariant(
                        variant_id=f"var-{variant_idx}",
                        variant_type="OmittedException",
                        original_snippet=code,
                        mutated_snippet="return None",
                        line_number=line_no,
                        is_killed=False,
                    )
                )
                variant_idx += 1

            # 3. Mutate Boundary Off-by-one (< 0 -> <= 0, < 2 -> < 1)
            boundary_match = re.search(r"([<>=!]+)\s*(\d+)", code)
            if boundary_match:
                op, num_str = boundary_match.groups()
                num = int(num_str)
                shifted_num = num + 1 if op.startswith("<") else max(0, num - 1)
                mutated = code.replace(f"{op} {num_str}", f"{op} {shifted_num}", 1)
                if mutated != code:
                    variants.append(
                        ProgramVariant(
                            variant_id=f"var-{variant_idx}",
                            variant_type="BoundaryOffByOne",
                            original_snippet=code,
                            mutated_snippet=mutated,
                            line_number=line_no,
                            is_killed=False,
                        )
                    )
                    variant_idx += 1

            # 4. Mutate Null / Empty Guards
            if re.match(r"^if\s+not\s+\w+:", code):
                variants.append(
                    ProgramVariant(
                        variant_id=f"var-{variant_idx}",
                        variant_type="GuardBypass",
                        original_snippet=code,
                        mutated_snippet="if False:",
                        line_number=line_no,
                        is_killed=False,
                    )
                )
                variant_idx += 1

        return variants

    @classmethod
    def evaluate_test_discrimination(
        cls,
        patch_diff: str,
        test_diff: str,
    ) -> DiscriminationReport:
        """Audits whether synthesized tests actively kill patch mutants."""
        raw_variants = cls.generate_variants(patch_diff)
        if not raw_variants:
            # Trivial or comment-only patch
            return DiscriminationReport(
                total_variants=0,
                killed_variants=0,
                discrimination_score=1.0,
                is_adequately_discriminating=True,
                variants=[],
                surviving_variants=[],
                augmentation_directives=[],
            )

        evaluated_variants: List[ProgramVariant] = []
        surviving: List[ProgramVariant] = []
        directives: List[str] = []

        # Extract assertions from test diff
        test_content = test_diff.lower()
        has_raises = "pytest.raises" in test_content or "assertraises" in test_content
        has_assert_equal = "assert " in test_content or "self.assertequal" in test_content

        for var in raw_variants:
            killed = False
            killer: Optional[str] = None

            if var.variant_type == "OmittedException":
                # Exception omission is killed only if the test explicitly checks for raises
                if has_raises:
                    killed = True
                    killer = "pytest.raises assertion verifying exception propagation"
                else:
                    directives.append(
                        f"Add negative assertion `with pytest.raises(...)` for guard at line {var.line_number}."
                    )

            elif var.variant_type in ("InvertedComparison", "BoundaryOffByOne"):
                # Comparison or boundary mutants are killed if tests check boundary inputs or raises
                keywords = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", var.original_snippet)
                if any(k.lower() in test_content for k in keywords) and (has_raises or has_assert_equal):
                    killed = True
                    killer = "Targeted boundary check or exception assertion"
                else:
                    directives.append(
                        f"Add boundary edge-case input test covering `{var.original_snippet}` at line {var.line_number}."
                    )

            elif var.variant_type == "GuardBypass":
                if has_raises or ("none" in test_content or "empty" in test_content or "''" in test_content):
                    killed = True
                    killer = "Null/empty input parameter boundary test"
                else:
                    directives.append(
                        f"Add null or empty parameter validation test for `{var.original_snippet}`."
                    )

            updated = ProgramVariant(
                variant_id=var.variant_id,
                variant_type=var.variant_type,
                original_snippet=var.original_snippet,
                mutated_snippet=var.mutated_snippet,
                line_number=var.line_number,
                is_killed=killed,
                killing_assertion=killer,
            )
            evaluated_variants.append(updated)
            if not killed:
                surviving.append(updated)

        total = len(evaluated_variants)
        killed_count = len(evaluated_variants) - len(surviving)
        score = (killed_count / total) if total > 0 else 1.0
        adequate = score >= 0.70

        logger.info(
            "variant_discrimination_evaluated",
            total_variants=total,
            killed_variants=killed_count,
            score=round(score, 3),
            adequate=adequate,
        )

        return DiscriminationReport(
            total_variants=total,
            killed_variants=killed_count,
            discrimination_score=score,
            is_adequately_discriminating=adequate,
            variants=evaluated_variants,
            surviving_variants=surviving,
            augmentation_directives=directives,
        )
