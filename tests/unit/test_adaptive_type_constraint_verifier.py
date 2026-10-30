"""Unit tests for AdaptiveTypeConstraintVerifier (PLDI 2025 / AdapTrack 2026)."""

import pytest
from services.adaptive_type_constraint_verifier import (
    AdaptiveTypeConstraintVerifier,
    TypeConstraintReport,
)


def test_adaptive_verifier_clean_cot_and_guard():
    response = (
        "<thought>\n"
        "1. Need to ensure ndigits is non-negative.\n"
        "2. ndigits is Optional[int], so check if not None first.\n"
        "</thought>\n"
        "```diff\n"
        "--- a/src/number.py\n"
        "+++ b/src/number.py\n"
        "@@ -196,3 +196,5 @@\n"
        "+    if ndigits is not None and ndigits < 0:\n"
        "+        raise ValueError('ndigits must be non-negative')\n"
        "```"
    )

    sig = "def intcomma(value: NumberOrString, ndigits: int | None = None) -> str:"
    report = AdaptiveTypeConstraintVerifier.verify_response(response, function_signature=sig)

    assert report.thought_tokens_preserved is True
    assert report.code_block_found is True
    assert report.type_safety_score == 1.0
    assert len(report.type_errors_detected) == 0


def test_adaptive_verifier_detects_unchecked_nullable_comparison():
    response = (
        "<thought>Direct comparison</thought>\n"
        "```diff\n"
        "+    if ndigits < 0:\n"
        "+        raise ValueError('must be positive')\n"
        "```"
    )

    sig = "def intcomma(value: str, ndigits: int | None = None) -> str:"
    report = AdaptiveTypeConstraintVerifier.verify_response(response, function_signature=sig)

    assert report.type_safety_score < 1.0
    assert any("Nullable parameter 'ndigits'" in err for err in report.type_errors_detected)
    assert len(report.recommendations) > 0


def test_adaptive_verifier_report_to_dict():
    rep = TypeConstraintReport(
        thought_tokens_preserved=True,
        code_block_found=True,
        type_errors_detected=[],
        type_safety_score=0.95,
        recommendations=["All safe"],
    )
    d = rep.to_dict()
    assert d["thought_tokens_preserved"] is True
    assert d["type_safety_score"] == 0.95
    assert len(d["recommendations"]) == 1
