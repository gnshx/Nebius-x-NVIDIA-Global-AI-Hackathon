"""Unit tests for RepoMedic's Semantic Patch Minimizer & Delta Debugging Engine."""

import pytest
from models.schemas import FileChange, Patch
from services.patch_minimizer import PatchMinimizer, PatchMetrics


def test_clean_hunk_diff_strips_trailing_whitespace():
    raw_diff = (
        "--- a/src/math.py\n"
        "+++ b/src/math.py\n"
        "@@ -10,3 +10,4 @@\n"
        " def add(a, b):   \n"
        "+    return a + b    \n"
    )
    cleaned = PatchMinimizer.clean_hunk_diff(raw_diff)
    lines = cleaned.splitlines()
    assert lines[3] == " def add(a, b):"
    assert lines[4] == "+    return a + b"


def test_clean_hunk_diff_normalizes_crlf_newlines():
    crlf_diff = "--- a/src/core.py\r\n+++ b/src/core.py\r\n@@ -1,2 +1,2 @@\r\n-val = 1\r\n+val = 2\r\n"
    cleaned = PatchMinimizer.clean_hunk_diff(crlf_diff)
    assert "\r" not in cleaned
    assert "+val = 2" in cleaned


def test_drops_noop_file_modifications():
    patch = Patch(
        summary="Fix index error",
        files=[
            FileChange(
                path="src/parser.py",
                operation="modify",
                patch="--- a/src/parser.py\n+++ b/src/parser.py\n@@ -1,5 +1,5 @@\n # No real logic change\n",
                reason="Unchanged comment",
            ),
            FileChange(
                path="src/utils.py",
                operation="modify",
                patch="--- a/src/utils.py\n+++ b/src/utils.py\n@@ -5,2 +5,3 @@\n-x = 1\n+x = 2\n",
                reason="Real bugfix",
            ),
        ],
    )

    minimized = PatchMinimizer.minimize(patch)
    assert len(minimized.files) == 1
    assert minimized.files[0].path == "src/utils.py"


def test_retains_create_operation_even_with_new_content():
    patch = Patch(
        summary="Add new module",
        files=[
            FileChange(
                path="src/new_mod.py",
                operation="create",
                patch="--- /dev/null\n+++ b/src/new_mod.py\n@@ -0,0 +1,3 @@\n+def hello():\n+    return 42\n",
                reason="New module",
            )
        ],
    )

    minimized = PatchMinimizer.minimize(patch)
    assert len(minimized.files) == 1
    assert minimized.files[0].path == "src/new_mod.py"


def test_evaluate_metrics_cleanliness_score():
    patch = Patch(
        summary="Atomic fix",
        files=[
            FileChange(
                path="src/validator.py",
                operation="modify",
                patch="--- a/src/validator.py\n+++ b/src/validator.py\n@@ -10,3 +10,5 @@\n+if x < 0:\n+    raise ValueError('negative')\n",
                reason="Add check",
            )
        ],
    )

    metrics = PatchMinimizer.evaluate_metrics(patch)
    assert metrics.total_files == 1
    assert metrics.lines_added == 2
    assert metrics.lines_removed == 0
    assert metrics.hunks_count == 1
    assert metrics.cleanliness_score >= 0.95


def test_empty_patch_handling():
    patch = Patch(summary="Empty test", files=[])
    minimized = PatchMinimizer.minimize(patch)
    assert len(minimized.files) == 0
    metrics = PatchMinimizer.evaluate_metrics(minimized)
    assert metrics.cleanliness_score == 1.0
