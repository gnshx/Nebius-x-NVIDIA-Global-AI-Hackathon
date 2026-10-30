"""Unit tests for RegressionInvariantProber (SWE-bench Atlas ICLR 2026)."""

import pytest
from services.regression_invariant_prober import RegressionInvariantProber, InvariantProbeReport


def test_invariant_prober_clean_module():
    source = (
        '__all__ = ["calc", "format_val"]\n\n'
        'def calc(x):\n'
        '    """Calculate double."""\n'
        '    return x * 2\n\n'
        'def format_val(val):\n'
        '    """Format output."""\n'
        '    return str(val)\n'
    )

    report = RegressionInvariantProber.probe_module_invariants(source, "src/calc.py")
    assert isinstance(report, InvariantProbeReport)
    assert report.invariants_preserved is True
    assert report.invariant_score == 1.0
    assert len(report.violations) == 0
    assert report.inspected_exports_count == 2


def test_invariant_prober_detects_missing_export_in_all():
    source = (
        '__all__ = ["calc", "deleted_function"]\n\n'
        'def calc(x):\n'
        '    return x * 2\n'
    )

    report = RegressionInvariantProber.probe_module_invariants(source, "src/mod.py")
    assert report.invariants_preserved is False
    assert any("deleted_function" in v for v in report.violations)
    assert report.invariant_score < 1.0


def test_invariant_prober_detects_unclosed_docstring_delimiter():
    source = (
        'def helper():\n'
        '    """This docstring is not closed\n'
        '    return 1\n'
    )

    report = RegressionInvariantProber.probe_module_invariants(source, "src/doc.py")
    assert report.invariants_preserved is False
    assert len(report.violations) > 0


def test_invariant_prober_empty_or_non_python():
    empty_report = RegressionInvariantProber.probe_module_invariants("")
    assert empty_report.invariants_preserved is True
    assert empty_report.invariant_score == 1.0

    js_report = RegressionInvariantProber.probe_module_invariants("const x = 1;", "src/app.js")
    assert js_report.invariants_preserved is True


def test_invariant_prober_to_dict():
    report = RegressionInvariantProber.probe_module_invariants("x = 1\n")
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "invariants_preserved" in d
    assert "invariant_score" in d
    assert "violations" in d
