"""Unit tests for Self-Supervised Dynamic Contract Fuzzer (SWE-Fuzz / FSE 2026)."""

import pytest
from services.contract_fuzzer import (
    DynamicContractFuzzer,
    ContractFuzzReport,
    FunctionContractAudit,
    FuzzTestCase,
)


def test_fuzzer_empty_source():
    report = DynamicContractFuzzer.audit_code("")
    assert report.is_robust is True
    assert report.overall_robustness_score == 1.0
    assert report.functions_audited == 0
    assert report.total_fuzz_cases == 0


def test_fuzzer_guarded_function():
    code = """
def format_user_name(name: str) -> str:
    if name is None:
        return ""
    if not isinstance(name, str):
        raise TypeError("name must be string")
    try:
        return name.strip().title()
    except Exception:
        return ""
"""
    report = DynamicContractFuzzer.audit_code(code, module_name="users")
    assert report.functions_audited == 1
    assert report.overall_robustness_score >= 0.70
    audit = report.function_audits[0]
    assert audit.function_name == "format_user_name"
    assert audit.has_none_guard is True
    assert audit.has_type_check is True
    assert audit.has_exception_handling is True
    assert len(audit.boundary_risks) == 0
    assert report.is_robust is True
    assert "test_fuzz_format_user_name_boundaries" in report.synthesized_property_test


def test_fuzzer_unguarded_function():
    code = """
def calculate_ratio(val, divisor):
    return val / divisor
"""
    report = DynamicContractFuzzer.audit_code(code, module_name="math_ops")
    assert report.functions_audited == 1
    audit = report.function_audits[0]
    assert audit.has_none_guard is False
    assert audit.has_type_check is False
    assert audit.has_exception_handling is False
    assert len(audit.boundary_risks) > 0
    assert report.is_robust is False
    assert any("val" in r for r in audit.boundary_risks)


def test_fuzzer_heuristic_fallback_on_diff_hunk():
    diff_hunk = """
@@ -10,3 +10,5 @@
+    if value is None:
+        return default
+    return str(value)
"""
    report = DynamicContractFuzzer.audit_code(diff_hunk)
    assert report.functions_audited == 1
    assert report.overall_robustness_score >= 0.70
    assert report.is_robust is True


def test_fuzzer_property_test_synthesis():
    code = """
def process_data(records):
    if records is None:
        return []
    return [r for r in records if r]
"""
    report = DynamicContractFuzzer.audit_code(code, module_name="pipeline")
    test_code = report.synthesized_property_test
    assert "@pytest.mark.parametrize" in test_code
    assert "test_fuzz_process_data_boundaries" in test_code
    assert "None, '', [], {}" in test_code
