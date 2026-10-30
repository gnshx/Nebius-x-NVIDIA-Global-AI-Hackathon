"""Unit tests for Differential Memory Profiling & Heap Hazard Guard (MemCheck-APR 2026)."""

import pytest
from services.memory_leak_guard import MemoryLeakGuard, MemoryAuditReport, MemoryHazard


def test_memory_guard_empty():
    report = MemoryLeakGuard.audit_code("")
    assert report.is_memory_safe is True
    assert report.safety_score == 1.0
    assert len(report.hazards_detected) == 0


def test_memory_guard_safe_code():
    code = """
def process_numbers(numbers: list[int]) -> list[int]:
    return [n * 2 for n in numbers if n > 0]
"""
    report = MemoryLeakGuard.audit_code(code)
    assert report.is_memory_safe is True
    assert report.safety_score == 1.0
    assert len(report.hazards_detected) == 0
    assert "Memory safety verified" in report.recommendation


def test_memory_guard_huge_allocation():
    code = """
def allocate_huge_buffer():
    buf = [0] * 50_000_000
    return buf
"""
    report = MemoryLeakGuard.audit_code(code)
    assert report.is_memory_safe is False
    assert report.safety_score < 0.70
    assert any(h.hazard_type == "HUGE_ALLOCATION" for h in report.hazards_detected)


def test_memory_guard_global_leak():
    code = """
_CACHE = {}

def get_item(k, v):
    global _CACHE
    _CACHE[k] = v
    return v
"""
    report = MemoryLeakGuard.audit_code(code)
    assert any(h.hazard_type == "GLOBAL_LEAK" for h in report.hazards_detected)


def test_memory_guard_diff_hunk_heuristic():
    diff_hunk = """
@@ -10,2 +10,4 @@
+    global items_registry
+    items_registry.append(item)
"""
    report = MemoryLeakGuard.audit_code(diff_hunk)
    assert any(h.hazard_type == "GLOBAL_LEAK" for h in report.hazards_detected)
