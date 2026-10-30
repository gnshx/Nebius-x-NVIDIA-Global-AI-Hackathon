"""
RepoMedic — Evolutionary Patch Mutator & EvoScale Optimizer (Satori-SWE 2026)

Inspired by:
"Satori-SWE: Evolutionary Test-Time Scaling for Software Engineering Agents" (2026).

Addresses the critical compute bottleneck in multi-turn APR:
Instead of generating independent trajectories from scratch or discarding
partial progress upon test failure, the mutator treats patch generation
as an evolutionary process:
1. Calculates multi-objective fitness for candidate patches:
   Fitness = w_pass * test_pass_rate + w_min * (1 - churn) + w_ast * syntax_score
2. Preserves high-fitness partial hunks across reflection iterations.
3. Guides directed mutation exclusively on failing hunks rather than rewriting entire files.
"""

from __future__ import annotations

import difflib
import re
from typing import NamedTuple, List, Dict, Any, Optional


class PatchCandidate(NamedTuple):
    __test__ = False
    patch_id: str
    diff_content: str
    iteration: int
    tests_passed: int
    tests_total: int
    syntax_valid: bool
    fitness_score: float
    retained_hunks: List[str]
    failing_hunks: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "diff_content": self.diff_content,
            "iteration": self.iteration,
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_total,
            "syntax_valid": self.syntax_valid,
            "fitness_score": round(self.fitness_score, 4),
            "retained_hunks_count": len(self.retained_hunks),
            "failing_hunks_count": len(self.failing_hunks),
        }


class EvolutionaryPatchMutator:
    """Manages population fitness and directed hunk crossover across APR iterations."""

    def __init__(
        self,
        weight_tests: float = 0.60,
        weight_minimality: float = 0.25,
        weight_syntax: float = 0.15,
    ) -> None:
        self.w_tests = weight_tests
        self.w_min = weight_minimality
        self.w_syntax = weight_syntax
        self._population: List[PatchCandidate] = []

    def evaluate_candidate(
        self,
        patch_id: str,
        diff_content: str,
        iteration: int,
        tests_passed: int,
        tests_total: int,
        syntax_valid: bool = True,
        error_context: str = "",
    ) -> PatchCandidate:
        """Evaluates and records a candidate patch in the evolutionary pool."""
        # 1. Pass rate score (0.0 to 1.0)
        pass_rate = (tests_passed / tests_total) if tests_total > 0 else 0.0

        # 2. Minimality score (penalize excessive hunk lines > 30 lines)
        added_lines = [
            line for line in diff_content.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        line_count = len(added_lines)
        minimality_score = max(0.0, 1.0 - (line_count / 40.0))

        # 3. Syntax validity score
        syntax_score = 1.0 if syntax_valid else 0.0

        # Composite fitness
        fitness = (
            (self.w_tests * pass_rate)
            + (self.w_min * minimality_score)
            + (self.w_syntax * syntax_score)
        )

        # Decompose hunks
        hunks = self._decompose_hunks(diff_content)
        retained: List[str] = []
        failing: List[str] = []

        if error_context:
            for hunk in hunks:
                # If error mentions symbols or files in this hunk, mark for mutation
                hunk_symbols = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", hunk)
                matched = any(sym.lower() in error_context.lower() for sym in hunk_symbols)
                if matched:
                    failing.append(hunk)
                else:
                    retained.append(hunk)
        else:
            retained = hunks

        candidate = PatchCandidate(
            patch_id=patch_id,
            diff_content=diff_content,
            iteration=iteration,
            tests_passed=tests_passed,
            tests_total=tests_total,
            syntax_valid=syntax_valid,
            fitness_score=fitness,
            retained_hunks=retained,
            failing_hunks=failing,
        )

        self._population.append(candidate)
        return candidate

    def select_best_parent(self) -> Optional[PatchCandidate]:
        """Selects the highest fitness individual from the evolutionary population."""
        if not self._population:
            return None
        return max(self._population, key=lambda c: c.fitness_score)

    def formulate_mutation_prompt(self, candidate: PatchCandidate, error_analysis: str) -> str:
        """Constructs an EvoScale mutation directive instructing the model to refine failing hunks."""
        lines = [
            f"### Evolutionary Test-Time Compute Refinement (Fitness: {candidate.fitness_score:.2f})",
            f"- Current Progress: {candidate.tests_passed}/{candidate.tests_total} tests passing.",
            "- Directed Mutation Strategy: Retain verified working hunks, exclusively mutate failing logic.",
        ]

        if candidate.retained_hunks:
            lines.append("\n**Preserved Stable Hunks (DO NOT REMOVE OR REVERT):**")
            for i, hunk in enumerate(candidate.retained_hunks, 1):
                preview = "\n".join(hunk.splitlines()[:5])
                lines.append(f"```diff\n{preview}\n```")

        if candidate.failing_hunks:
            lines.append("\n**Target Hunks Requiring Mutation:**")
            for i, hunk in enumerate(candidate.failing_hunks, 1):
                lines.append(f"```diff\n{hunk}\n```")

        lines.append(f"\n**Root Cause / Traceback Feedback:**\n{error_analysis}")
        lines.append("\nGenerate the mutated unified diff addressing solely the failing conditions.")
        return "\n".join(lines)

    @staticmethod
    def _decompose_hunks(diff_content: str) -> List[str]:
        """Splits a unified diff into discrete diff hunks starting with @@."""
        hunks: List[str] = []
        current: List[str] = []
        in_hunk = False

        for line in diff_content.splitlines():
            if line.startswith("@@"):
                if current:
                    hunks.append("\n".join(current))
                    current = []
                in_hunk = True
            if in_hunk:
                current.append(line)

        if current:
            hunks.append("\n".join(current))
        elif not hunks and diff_content.strip():
            hunks.append(diff_content.strip())
        return hunks
