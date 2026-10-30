"""Unit tests for SpectrumFaultLocalizer (Ochiai & DStar SBFL)."""

import pytest
from services.spectrum_fault_localizer import SpectrumFaultLocalizer, SuspiciousLocation


def test_ochiai_and_dstar_perfect_suspiciousness():
    # 5 failed, 0 passed, total failed = 5
    ochiai = SpectrumFaultLocalizer.calculate_ochiai(failed_e=5, passed_e=0, total_failed=5)
    dstar = SpectrumFaultLocalizer.calculate_dstar(failed_e=5, passed_e=0, total_failed=5)

    assert ochiai == 1.0
    assert dstar == 25.0  # 5^2 / (0 + 0)


def test_ochiai_zero_failed():
    ochiai = SpectrumFaultLocalizer.calculate_ochiai(failed_e=0, passed_e=10, total_failed=5)
    dstar = SpectrumFaultLocalizer.calculate_dstar(failed_e=0, passed_e=10, total_failed=5)

    assert ochiai == 0.0
    assert dstar == 0.0


def test_localize_from_tracebacks_extracts_primary_culprit():
    tracebacks = [
        (
            'Traceback (most recent call last):\n'
            '  File "/workspace/humanize/src/humanize/number.py", line 198, in intcomma\n'
            '    result = f"{value:,.{ndigits}f}"\n'
            'ValueError: Format specifier missing precision\n'
        ),
        (
            'Traceback (most recent call last):\n'
            '  File "/workspace/humanize/src/humanize/number.py", line 198, in intcomma\n'
            '    result = f"{value:,.{ndigits}f}"\n'
            'ValueError: Format specifier missing precision\n'
        ),
    ]

    results = SpectrumFaultLocalizer.localize_from_tracebacks(
        failing_tracebacks=tracebacks,
        total_failed_tests=2,
        passing_locations={"/workspace/humanize/src/humanize/number.py:intcomma": 1},
    )

    assert len(results) == 1
    top = results[0]
    assert top.is_primary_culprit is True
    assert "number.py" in top.file_path
    assert top.function_name == "intcomma"
    assert top.line_number == 198
    assert top.ochiai_score > 0.80
    assert top.failed_count == 2
    assert top.passed_count == 1


def test_localize_from_tracebacks_empty():
    results = SpectrumFaultLocalizer.localize_from_tracebacks(
        failing_tracebacks=[], total_failed_tests=0
    )
    assert results == []


def test_suspicious_location_to_dict():
    loc = SuspiciousLocation(
        file_path="src/calc.py",
        function_name="divide",
        line_number=42,
        ochiai_score=0.9234,
        dstar_score=16.5,
        failed_count=4,
        passed_count=1,
        is_primary_culprit=True,
    )
    d = loc.to_dict()
    assert d["function_name"] == "divide"
    assert d["ochiai_score"] == 0.9234
    assert d["is_primary_culprit"] is True
