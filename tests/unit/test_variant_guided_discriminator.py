"""Unit tests for VariantGuidedDiscriminator (PROBE, ASE 2026)."""

import pytest
from services.variant_guided_discriminator import (
    VariantGuidedDiscriminator,
    ProgramVariant,
    DiscriminationReport,
)


def test_variant_generator_identifies_semantic_mutants():
    patch_diff = (
        "--- a/src/number.py\n"
        "+++ b/src/number.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+    if ndigits < 0:\n"
        "+        raise ValueError('ndigits must be non-negative')\n"
    )
    variants = VariantGuidedDiscriminator.generate_variants(patch_diff)
    assert len(variants) >= 2

    types = {v.variant_type for v in variants}
    assert "InvertedComparison" in types or "BoundaryOffByOne" in types
    assert "OmittedException" in types


def test_evaluate_test_discrimination_kills_mutants_with_pytest_raises():
    patch_diff = (
        "--- a/src/number.py\n"
        "+++ b/src/number.py\n"
        "@@ -10,3 +10,6 @@\n"
        "+    if ndigits < 0:\n"
        "+        raise ValueError('ndigits must be non-negative')\n"
    )
    test_diff = (
        "--- a/tests/test_number.py\n"
        "+++ b/tests/test_number.py\n"
        "@@ -50,3 +50,7 @@\n"
        "+def test_intcomma_negative_ndigits():\n"
        "+    with pytest.raises(ValueError):\n"
        "+        intcomma(1234, ndigits=-1)\n"
    )

    report = VariantGuidedDiscriminator.evaluate_test_discrimination(patch_diff, test_diff)
    assert report.total_variants >= 2
    assert report.killed_variants >= 2
    assert report.discrimination_score >= 0.70
    assert report.is_adequately_discriminating is True
    assert len(report.surviving_variants) == 0


def test_evaluate_test_discrimination_flags_surviving_variants():
    patch_diff = (
        "--- a/src/auth.py\n"
        "+++ b/src/auth.py\n"
        "@@ -15,3 +15,6 @@\n"
        "+    if not token:\n"
        "+        raise ValueError('missing token')\n"
    )
    # Weak test diff only testing happy path (no raises assertion)
    weak_test_diff = (
        "--- a/tests/test_auth.py\n"
        "+++ b/tests/test_auth.py\n"
        "@@ -20,2 +20,4 @@\n"
        "+def test_auth_happy():\n"
        "+    pass\n"
    )

    report = VariantGuidedDiscriminator.evaluate_test_discrimination(patch_diff, weak_test_diff)
    assert report.total_variants >= 1
    assert len(report.surviving_variants) >= 1
    assert report.is_adequately_discriminating is False
    assert len(report.augmentation_directives) > 0


def test_variant_discrimination_empty_patch():
    report = VariantGuidedDiscriminator.evaluate_test_discrimination("", "")
    assert report.total_variants == 0
    assert report.discrimination_score == 1.0
    assert report.is_adequately_discriminating is True


def test_discrimination_report_to_dict():
    v = ProgramVariant("v1", "InvertedComparison", "x < 0", "x >= 0", 12, True, "test")
    rep = DiscriminationReport(
        total_variants=1,
        killed_variants=1,
        discrimination_score=1.0,
        is_adequately_discriminating=True,
        variants=[v],
        surviving_variants=[],
        augmentation_directives=[],
    )
    d = rep.to_dict()
    assert d["total_variants"] == 1
    assert d["killed_variants"] == 1
    assert d["discrimination_score"] == 1.0
    assert d["surviving_variants_count"] == 0
