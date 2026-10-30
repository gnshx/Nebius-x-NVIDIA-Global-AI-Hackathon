"""Unit tests for RepoMedic's ContextSlicer (CODESTRUCT)."""

import pytest
from services.context_slicer import ContextSlicer, SlicedContextResult


def test_compact_code_content_normalizes_blanks():
    raw = "def foo():\n\n\n\n    return 42\n"
    compact = ContextSlicer.compact_code_content(raw)
    assert "\n\n\n" not in compact
    assert "return 42" in compact


def test_slice_chunks_prioritizes_target_symbols():
    chunks = [
        {
            "path": "src/number.py",
            "symbol": "intcomma",
            "chunk_type": "function",
            "content": "def intcomma(value, ndigits=None):\n    pass\n",
        },
        {
            "path": "src/time.py",
            "symbol": "naturaltime",
            "chunk_type": "function",
            "content": "def naturaltime(date):\n    pass\n",
        },
        {
            "path": "tests/test_number.py",
            "symbol": "test_intcomma",
            "chunk_type": "function",
            "content": "def test_intcomma():\n    assert True\n",
        },
    ]

    result = ContextSlicer.slice_chunks(
        chunks,
        target_symbols=["intcomma"],
        max_tokens=1000,
    )

    assert isinstance(result, SlicedContextResult)
    assert len(result.sliced_chunks) == 3
    # First chunk should have highest priority
    assert result.sliced_chunks[0]["symbol"] == "intcomma"
    assert result.sliced_chunks[0]["priority_score"] >= 4.0
    assert "intcomma" in result.retained_symbols
    assert result.context_density_score >= 0.80


def test_slice_chunks_respects_token_limit():
    large_content = "def big_func():\n" + ("    x = 1\n" * 200)
    chunks = [
        {
            "path": "src/big.py",
            "symbol": "big_func",
            "chunk_type": "function",
            "content": large_content,
        },
        {
            "path": "src/small.py",
            "symbol": "small_func",
            "chunk_type": "function",
            "content": "def small_func(): return 1",
        },
    ]

    # Limit to 50 tokens
    result = ContextSlicer.slice_chunks(chunks, target_symbols=["big_func"], max_tokens=50)

    assert result.sliced_token_count <= 60
    assert result.compression_ratio > 0.50


def test_slice_chunks_to_dict():
    chunks = [{"path": "src/a.py", "symbol": "a", "chunk_type": "function", "content": "x = 1"}]
    result = ContextSlicer.slice_chunks(chunks)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "sliced_chunks" in d
    assert "compression_ratio" in d
    assert "context_density_score" in d
