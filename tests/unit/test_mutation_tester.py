"""Unit tests for RepoMedic's Test Mutation & Discriminative Oracle Validator."""

import pytest
from services.mutation_tester import MutationTester, TestQualityReport


def test_mutation_tester_detects_tautological_assertions():
    diff_with_tautology = """
--- a/tests/test_dummy.py
+++ b/tests/test_dummy.py
@@ -10,3 +10,6 @@
+def test_something():
+    assert True
+    assert x == x
+    assert len(items) == len(items)
"""
    report = MutationTester.audit_test_diff(diff_with_tautology)

    assert report.total_test_functions == 1
    assert report.tautological_assertions == 3
    assert report.is_robust_oracle is False
    assert any("tautological" in f for f in report.findings)


def test_mutation_tester_valid_assertions():
    diff_valid = """
--- a/tests/test_number.py
+++ b/tests/test_number.py
@@ -40,3 +40,7 @@
+def test_intcomma_negative():
+    assert intcomma(1234, ndigits=2) == "1,234.00"
+    assert intcomma(-500) == "-500"
"""
    report = MutationTester.audit_test_diff(diff_valid)

    assert report.total_test_functions == 1
    assert report.valid_assertions == 2
    assert report.tautological_assertions == 0
    assert report.is_robust_oracle is True
    assert report.discrimination_score >= 0.85


def test_mutation_tester_recognizes_pytest_raises():
    diff_raises = """
--- a/tests/test_number.py
+++ b/tests/test_number.py
@@ -50,3 +50,6 @@
+def test_negative_ndigits_raises():
+    with pytest.raises(ValueError, match="ndigits must be non-negative"):
+        intcomma(123, ndigits=-1)
"""
    report = MutationTester.audit_test_diff(diff_raises)

    assert report.total_test_functions == 1
    assert report.has_exception_testing is True
    assert report.valid_assertions >= 1
    assert report.is_robust_oracle is True


def test_mutation_tester_empty_or_zero_assertions():
    diff_empty = """
--- a/tests/test_empty.py
+++ b/tests/test_empty.py
@@ -1,3 +1,5 @@
+def test_no_asserts():
+    pass
"""
    report = MutationTester.audit_test_diff(diff_empty)

    assert report.valid_assertions == 0
    assert report.is_robust_oracle is False
    assert report.discrimination_score < 0.50
    assert any("zero valid assert" in f for f in report.findings)


def test_mutation_tester_to_dict_serialization():
    diff = """
+def test_one():
+    assert 1 == 2
"""
    report = MutationTester.audit_test_diff(diff)
    d = report.to_dict()

    assert isinstance(d, dict)
    assert "discrimination_score" in d
    assert "is_robust_oracle" in d
    assert "tautological_assertions" in d
