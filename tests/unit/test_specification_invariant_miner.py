"""Unit tests for SpecificationInvariantMiner (VibeRepair 2026)."""

import pytest
from services.specification_invariant_miner import SpecificationInvariantMiner, SpecificationReport


def test_specification_miner_infers_non_negative_precondition():
    miner = SpecificationInvariantMiner()
    specs = miner.mine_specifications(
        issue_description="intcomma crashes with negative ndigits=-1 precision error"
    )
    assert any("non-negative" in s for s in specs)


def test_specification_miner_audits_clean_guard_patch():
    miner = SpecificationInvariantMiner()
    diff = (
        "--- a/src/number.py\n+++ b/src/number.py\n"
        "@@ -50,3 +50,6 @@\n"
        "+    if ndigits is not None and ndigits < 0:\n"
        "+        raise ValueError('ndigits must be non-negative')\n"
    )
    report = miner.audit_patch_contract(
        diff_content=diff,
        issue_description="intcomma crashes with negative ndigits",
        traceback_text="ValueError: Format specifier missing precision",
    )

    assert report.has_explicit_guard is True
    assert report.contract_adherence_score == 1.0
    assert len(report.violations) == 0
    assert "satisfies all mined behavioral contracts" in report.recommendation


def test_specification_miner_flags_missing_precondition():
    miner = SpecificationInvariantMiner()
    diff = (
        "--- a/src/number.py\n+++ b/src/number.py\n"
        "@@ -50,3 +50,5 @@\n"
        "+    return str(value)\n"
    )
    report = miner.audit_patch_contract(
        diff_content=diff,
        issue_description="intcomma crashes with negative ndigits=-1",
    )

    assert report.has_explicit_guard is False
    assert report.contract_adherence_score <= 0.50
    assert any("Missing non-negative precondition check" in v for v in report.violations)


def test_specification_miner_report_to_dict():
    rep = SpecificationReport(
        inferred_preconditions=["Precondition: x >= 0"],
        inferred_postconditions=["Postcondition: returns int"],
        has_explicit_guard=True,
        contract_adherence_score=0.95,
        violations=[],
        recommendation="Approved",
    )
    d = rep.to_dict()
    assert d["has_explicit_guard"] is True
    assert d["contract_adherence_score"] == 0.95
    assert len(d["inferred_preconditions"]) == 1
