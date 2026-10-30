"""Unit tests for RepoMedic's MultiCandidateReranker."""

import pytest
from services.candidate_reranker import MultiCandidateReranker, RerankingResult


def test_reranker_selects_atomic_patch_over_bloated_patch():
    patch_atomic = {
        "summary": "Atomic 3-line input validation",
        "files": [
            {
                "path": "src/number.py",
                "diff": "@@ -50,3 +50,6 @@\n+    if ndigits is not None and ndigits < 0:\n+        raise ValueError('ndigits must be non-negative')",
            }
        ],
    }

    patch_bloated = {
        "summary": "Bloated multi-file overhaul",
        "files": [
            {"path": f"src/file_{i}.py", "diff": "@@ -1,1 +1,40 @@\n" + ("+ line\n" * 40)}
            for i in range(5)
        ],
    }

    result = MultiCandidateReranker.rerank([patch_bloated, patch_atomic])

    assert isinstance(result, RerankingResult)
    assert result.total_candidates_evaluated == 2
    assert result.champion_patch["summary"] == "Atomic 3-line input validation"
    assert result.candidates[0].rank == 1
    assert result.candidates[0].composite_score > result.candidates[1].composite_score


def test_reranker_penalizes_invariant_violation():
    patch_clean = {
        "summary": "Clean fix",
        "files": [{"path": "src/calc.py", "diff": "+    x += 1"}],
    }
    patch_skip = {
        "summary": "Cheat fix with test skip",
        "files": [{"path": "tests/test_calc.py", "diff": "+@pytest.mark.skip\ndef test_bad():"}],
    }

    result = MultiCandidateReranker.rerank([patch_skip, patch_clean])

    assert result.champion_patch["summary"] == "Clean fix"
    assert result.candidates[1].invariant_score <= 0.20


def test_reranker_handles_empty_candidates():
    result = MultiCandidateReranker.rerank([])
    assert result.total_candidates_evaluated == 0
    assert result.champion_patch["summary"] == "Empty"


def test_reranker_to_dict():
    patch = {"summary": "Simple", "files": [{"path": "src/a.py", "diff": "+x = 1"}]}
    result = MultiCandidateReranker.rerank([patch])
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "champion_patch" in d
    assert "candidates" in d
