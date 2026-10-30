"""Unit tests for Context-Pruned Bi-Directional Program Slicing (CausalRepair 2026)."""

import pytest
from services.bidirectional_program_slicer import (
    BiDirectionalProgramSlicer,
    SlicedContext,
)


def test_slice_empty_file():
    slicer = BiDirectionalProgramSlicer()
    result = slicer.slice_code("", target_line=1)
    assert result.original_line_count == 0
    assert result.sliced_line_count == 0
    assert result.compression_ratio == 0.0
    assert result.sliced_code == ""


def test_slice_retains_imports_and_target_method():
    slicer = BiDirectionalProgramSlicer()
    source_code = """import os
import sys
from typing import List

class DataProcessor:
    def helper_unrelated(self):
        a = 1
        b = 2
        c = 3
        return a + b + c

    def compute_summary(self, items: List[int]) -> int:
        multiplier = 2
        total = 0
        for item in items:
            total += item * multiplier
        return total
"""
    # Target line is inside compute_summary (e.g. line 17: total += item * multiplier)
    lines = source_code.splitlines()
    target_line = None
    for idx, l in enumerate(lines, 1):
        if "total += item * multiplier" in l:
            target_line = idx
            break
    assert target_line is not None

    slice_res = slicer.slice_code(source_code, target_line=target_line, context_radius=3)
    assert slice_res.original_line_count == len(lines)
    assert slice_res.sliced_line_count < slice_res.original_line_count
    assert slice_res.compression_ratio > 0.0

    # Retains top-level imports
    assert "import os" in slice_res.sliced_code
    assert "from typing import List" in slice_res.sliced_code

    # Retains class header
    assert "class DataProcessor:" in slice_res.sliced_code

    # Prunes unrelated helper body
    assert "[pruned" in slice_res.sliced_code

    # Retains target line and compute_summary
    assert "def compute_summary" in slice_res.sliced_code
    assert "total += item * multiplier" in slice_res.sliced_code


def test_slice_backward_def_use_capture():
    slicer = BiDirectionalProgramSlicer()
    # config_multiplier is defined far above target line (beyond small context_radius)
    source_code = """
def run_pipeline(x: int) -> int:
    config_multiplier = 42
    # Many filler lines
    line1 = 1
    line2 = 2
    line3 = 3
    line4 = 4
    line5 = 5
    line6 = 6
    line7 = 7
    line8 = 8
    line9 = 9
    line10 = 10
    result = x * config_multiplier
    return result
"""
    lines = source_code.splitlines()
    target_line = None
    for idx, l in enumerate(lines, 1):
        if "result = x * config_multiplier" in l:
            target_line = idx
            break
    assert target_line is not None

    # Use small context radius of 2 so config_multiplier is far outside window
    slice_res = slicer.slice_code(source_code, target_line=target_line, context_radius=2)

    # Backward slicing must retain the definition of config_multiplier!
    assert "config_multiplier = 42" in slice_res.sliced_code
    assert "result = x * config_multiplier" in slice_res.sliced_code
    assert "return result" in slice_res.sliced_code


def test_slice_compression_ratio():
    slicer = BiDirectionalProgramSlicer()
    code_lines = ["import math"]
    for i in range(1, 100):
        code_lines.append(f"def unused_func_{i}():\n    return {i}")
    code_lines.append("def target_func():\n    val = 123\n    return val")
    source_code = "\n".join(code_lines)

    target_line = len(source_code.splitlines()) - 1
    slice_res = slicer.slice_code(source_code, target_line=target_line, context_radius=5)

    assert slice_res.compression_ratio > 0.50
    assert "import math" in slice_res.sliced_code
    assert "def target_func():" in slice_res.sliced_code


def test_fallback_syntax_error():
    slicer = BiDirectionalProgramSlicer()
    broken_code = """def broken(:
    x = 1
    y = 2
    z = 3
    return x
"""
    slice_res = slicer.slice_code(broken_code, target_line=3, context_radius=1)
    assert slice_res.sliced_line_count > 0
    assert "y = 2" in slice_res.sliced_code
