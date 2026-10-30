"""Unit tests for EvolutionaryPatchMutator (Satori-SWE EvoScale 2026)."""

import pytest
from services.evolutionary_patch_mutator import EvolutionaryPatchMutator, PatchCandidate


def test_evolutionary_evaluates_candidate_high_fitness():
    mutator = EvolutionaryPatchMutator()
    diff = (
        "--- a/src/math.py\n+++ b/src/math.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+    if x < 0:\n"
        "+        raise ValueError('x must be positive')\n"
    )
    candidate = mutator.evaluate_candidate(
        patch_id="p1",
        diff_content=diff,
        iteration=1,
        tests_passed=10,
        tests_total=10,
        syntax_valid=True,
    )

    assert candidate.fitness_score > 0.85
    assert candidate.tests_passed == 10
    assert candidate.syntax_valid is True
    assert len(candidate.retained_hunks) == 1
    assert len(candidate.failing_hunks) == 0


def test_evolutionary_identifies_failing_hunks_from_error_context():
    mutator = EvolutionaryPatchMutator()
    diff = (
        "--- a/src/user.py\n+++ b/src/user.py\n"
        "@@ -5,3 +5,5 @@\n"
        "+    def parse_token():\n"
        "+        return 42\n"
    )
    candidate = mutator.evaluate_candidate(
        patch_id="p2",
        diff_content=diff,
        iteration=1,
        tests_passed=5,
        tests_total=10,
        syntax_valid=True,
        error_context="IndexError in parse_token line 7",
    )

    assert candidate.fitness_score < 0.80
    assert len(candidate.failing_hunks) == 1


def test_evolutionary_selects_best_parent():
    mutator = EvolutionaryPatchMutator()
    mutator.evaluate_candidate("p1", "diff1", 1, tests_passed=2, tests_total=10)
    mutator.evaluate_candidate("p2", "diff2", 2, tests_passed=9, tests_total=10)
    mutator.evaluate_candidate("p3", "diff3", 3, tests_passed=4, tests_total=10)

    best = mutator.select_best_parent()
    assert best is not None
    assert best.patch_id == "p2"
    assert best.tests_passed == 9


def test_evolutionary_mutation_prompt_formulation():
    mutator = EvolutionaryPatchMutator()
    candidate = mutator.evaluate_candidate(
        patch_id="p_test",
        diff_content="@@ -1,2 +1,3 @@\n+    token = parts[0]\n",
        iteration=1,
        tests_passed=14,
        tests_total=16,
        syntax_valid=True,
        error_context="AssertionError: token empty",
    )

    prompt = mutator.formulate_mutation_prompt(candidate, "Token check failed on empty string")
    assert "Evolutionary Test-Time Compute Refinement" in prompt
    assert "Token check failed on empty string" in prompt
    assert "Directed Mutation Strategy" in prompt


def test_evolutionary_candidate_to_dict():
    cand = PatchCandidate(
        patch_id="dict_test",
        diff_content="diff",
        iteration=1,
        tests_passed=5,
        tests_total=5,
        syntax_valid=True,
        fitness_score=0.95,
        retained_hunks=["hunk1"],
        failing_hunks=[],
    )
    d = cand.to_dict()
    assert d["patch_id"] == "dict_test"
    assert d["fitness_score"] == 0.95
    assert d["retained_hunks_count"] == 1
    assert d["failing_hunks_count"] == 0
