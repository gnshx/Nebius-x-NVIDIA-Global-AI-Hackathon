"""Unit tests for resilient unified patch application in LocalSandboxExecutor."""

import tempfile
from pathlib import Path
import pytest

from services.nebius.local_sandbox import _apply_unified_patch_to_dir


def test_apply_unified_patch_empty():
    with tempfile.TemporaryDirectory() as td:
        assert _apply_unified_patch_to_dir(Path(td), "") is False
        assert _apply_unified_patch_to_dir(Path(td), "   \n") is False


def test_apply_unified_patch_creates_new_file():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        patch = """--- /dev/null
+++ b/src/hello.py
@@ -0,0 +1,3 @@
+def greet(name: str) -> str:
+    return f"Hello, {name}!"
+
"""
        res = _apply_unified_patch_to_dir(workdir, patch)
        assert res is True
        created_file = workdir / "src" / "hello.py"
        assert created_file.exists()
        content = created_file.read_text(encoding="utf-8")
        assert "def greet(name: str) -> str:" in content
        assert 'return f"Hello, {name}!"' in content


def test_apply_unified_patch_modifies_asymmetric_hunk():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        target = workdir / "calc.py"
        target.write_text("""def divide(a: int, b: int) -> float:
    return a / b
""", encoding="utf-8")

        # Asymmetric hunk: replacing 1 line with 4 lines (adding ZeroDivisionError check)
        patch = """--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,5 @@
 def divide(a: int, b: int) -> float:
-    return a / b
+    if b == 0:
+        raise ValueError("Division by zero")
+    return a / b
"""
        res = _apply_unified_patch_to_dir(workdir, patch)
        assert res is True
        updated = target.read_text(encoding="utf-8")
        assert "if b == 0:" in updated
        assert 'raise ValueError("Division by zero")' in updated
        assert "return a / b" in updated


def test_apply_unified_patch_pure_addition():
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        target = workdir / "utils.py"
        target.write_text("""def existing_func():
    return 1
""", encoding="utf-8")

        # Adding a second function without deleting anything
        patch = """--- a/utils.py
+++ b/utils.py
@@ -2,1 +2,4 @@
     return 1
+
+def added_func():
+    return 2
"""
        res = _apply_unified_patch_to_dir(workdir, patch)
        assert res is True
        updated = target.read_text(encoding="utf-8")
        assert "def existing_func():" in updated
        assert "def added_func():" in updated
        assert "return 2" in updated
