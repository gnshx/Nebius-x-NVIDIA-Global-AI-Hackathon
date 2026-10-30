"""Unit tests for Deterministic Patch Canonicalizer (CanonicalPatch, FSE 2026)."""

import pytest
from services.patch_canonicalizer import (
    DeterministicPatchCanonicalizer,
    CanonicalPatchReport,
)


def test_canonicalize_empty_diff():
    canonicalizer = DeterministicPatchCanonicalizer()
    report = canonicalizer.canonicalize_diff("")
    assert report.has_modifications is False
    assert report.canonical_diff == ""


def test_canonicalize_import_sorting():
    canonicalizer = DeterministicPatchCanonicalizer()
    diff = """--- a/src/math.py
+++ b/src/math.py
@@ -1,3 +1,7 @@
 import base
+from services.logger import log
+import sys
+import pytest
+import os
 def calculate():
     pass
"""
    report = canonicalizer.canonicalize_diff(diff)
    assert report.has_modifications is True
    assert report.imports_sorted_count > 0

    lines = report.canonical_diff.splitlines()
    # Check that stdlib imports (+import os, +import sys) appear before +import pytest
    # and +from services.logger appears last (local import)
    os_idx = lines.index("+import os")
    sys_idx = lines.index("+import sys")
    pytest_idx = lines.index("+import pytest")
    services_idx = lines.index("+from services.logger import log")

    assert os_idx < pytest_idx
    assert sys_idx < pytest_idx
    assert pytest_idx < services_idx


def test_canonicalize_trailing_whitespace():
    canonicalizer = DeterministicPatchCanonicalizer()
    diff = """--- a/src/math.py
+++ b/src/math.py
@@ -10,3 +10,4 @@
 def calculate():
-    return 1
+    val = 42    
+    return val
"""
    report = canonicalizer.canonicalize_diff(diff)
    assert report.has_modifications is True
    assert report.whitespace_cleanups_count >= 1
    assert "+    val = 42" in report.canonical_diff
    assert "+    val = 42    " not in report.canonical_diff


def test_canonicalize_consecutive_blank_lines():
    canonicalizer = DeterministicPatchCanonicalizer()
    diff = """--- a/src/math.py
+++ b/src/math.py
@@ -5,2 +5,6 @@
 def a(): pass
+
+
+
+def b(): pass
"""
    report = canonicalizer.canonicalize_diff(diff)
    assert report.has_modifications is True
    assert report.blank_lines_normalized_count >= 1
    # Should only have one + blank line before def b
    count_blank_adds = sum(1 for l in report.canonical_diff.splitlines() if l == "+")
    assert count_blank_adds == 1


def test_canonicalize_deduplicates_imports():
    canonicalizer = DeterministicPatchCanonicalizer()
    diff = """--- a/src/math.py
+++ b/src/math.py
@@ -1,2 +1,4 @@
+import json
+import json
 def a(): pass
"""
    report = canonicalizer.canonicalize_diff(diff)
    assert report.has_modifications is True
    assert report.canonical_diff.count("+import json") == 1
