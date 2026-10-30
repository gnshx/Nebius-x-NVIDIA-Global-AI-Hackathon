"""Unit tests for IssueLocalizationReranker (SweRank 2026)."""

import pytest
from services.issue_localization_reranker import IssueLocalizationReranker, LocalizationReport, RankedChunk


def test_issue_localization_prioritizes_traceback_frame():
    chunks = [
        {"path": "src/utils.py", "symbol": "helper", "chunk_type": "function", "content": "def helper(): pass"},
        {"path": "src/humanize/number.py", "symbol": "intcomma", "chunk_type": "function", "content": "def intcomma(val): pass"},
        {"path": "tests/test_number.py", "symbol": "test_it", "chunk_type": "function", "content": "def test_it(): pass"},
    ]

    issue_title = "intcomma() crashes with ValueError when ndigits < 0"
    issue_body = (
        "Traceback (most recent call last):\n"
        '  File "src/humanize/number.py", line 70, in intcomma\n'
        "ValueError: Format specifier missing precision\n"
    )

    report = IssueLocalizationReranker.rerank_chunks(
        chunks,
        issue_title=issue_title,
        issue_body=issue_body,
        likely_components=["number", "intcomma"],
    )

    assert isinstance(report, LocalizationReport)
    assert len(report.ranked_chunks) == 3
    # Top ranked chunk must be src/humanize/number.py
    assert report.ranked_chunks[0]["path"] == "src/humanize/number.py"
    assert report.top_localized_files[0] == "src/humanize/number.py"
    assert report.is_definitive is True
    assert report.localization_confidence >= 0.70


def test_issue_localization_empty_chunks():
    report = IssueLocalizationReranker.rerank_chunks([])
    assert report.ranked_chunks == []
    assert report.localization_confidence == 0.0
    assert report.is_definitive is False


def test_issue_localization_symbol_call_matching():
    chunks = [
        {"path": "src/parser.py", "symbol": "parse_args", "chunk_type": "function", "content": "def parse_args(): pass"},
        {"path": "src/lexer.py", "symbol": "tokenize", "chunk_type": "function", "content": "def tokenize(): pass"},
    ]

    report = IssueLocalizationReranker.rerank_chunks(
        chunks,
        issue_title="Bug in tokenize() function",
        issue_body="Calling tokenize() with empty string throws IndexError",
    )

    assert report.ranked_chunks[0]["symbol"] == "tokenize"
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "ranked_chunks" in d
    assert "top_localized_files" in d
    assert "localization_confidence" in d
