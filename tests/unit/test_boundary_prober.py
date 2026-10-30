"""Unit tests for RepoMedic's BoundaryProber (PROBE)."""

import pytest
from services.boundary_prober import BoundaryProber, BoundaryProbingResult


def test_probe_function_identifies_numeric_and_null_boundaries():
    code = """
def intcomma(value, ndigits=None):
    if ndigits is not None and ndigits < 0:
        raise ValueError("ndigits must be non-negative")
    return str(value)
"""
    result = BoundaryProber.probe_function(code, target_function="intcomma")

    assert isinstance(result, BoundaryProbingResult)
    assert result.function_name == "intcomma"
    assert result.total_probes >= 3

    # Check for negative ndigits probe
    neg_probes = [p for p in result.probes if p.parameter_name == "ndigits" and p.edge_value_repr == "-1"]
    assert len(neg_probes) == 1
    assert "Negative boundary" in neg_probes[0].rationale
    assert neg_probes[0].expected_behavior == "RAISE_VALUE_ERROR"

    # Check for None probe
    none_probes = [p for p in result.probes if p.edge_value_repr == "None"]
    assert len(none_probes) >= 1
    assert result.edge_coverage_score >= 0.70


def test_probe_function_string_and_container_boundaries():
    code = """
def process_data(elements, pattern):
    return [e for e in elements if pattern in e]
"""
    result = BoundaryProber.probe_function(code)

    assert result.function_name == "process_data"
    # Container boundary: []
    empty_list = [p for p in result.probes if p.edge_value_repr == "[]"]
    assert len(empty_list) == 1

    # String boundary: ""
    empty_str = [p for p in result.probes if p.edge_value_repr == '""']
    assert len(empty_str) == 1


def test_probe_function_no_defs():
    result = BoundaryProber.probe_function("x = 1\ny = 2")
    assert result.total_probes == 0
    assert result.edge_coverage_score == 0.0


def test_probe_function_to_dict():
    code = "def foo(count=0): pass"
    result = BoundaryProber.probe_function(code)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "function_name" in d
    assert "probes" in d
    assert "edge_coverage_score" in d
