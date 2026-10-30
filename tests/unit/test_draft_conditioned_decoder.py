"""Unit tests for DraftConditionedDecoder (DCCD, ICML 2026)."""

import pytest
from services.draft_conditioned_decoder import (
    DraftConditionedDecoder,
    DecodedCodeBlock,
)


def test_dccd_isolates_thought_trace_and_valid_code():
    raw_output = (
        "<thought>\n"
        "We need to add a check for negative ndigits.\n"
        "</thought>\n"
        "```python\n"
        "def intcomma(val, ndigits=0):\n"
        "    if ndigits < 0:\n"
        "        raise ValueError('ndigits must be non-negative')\n"
        "    return str(val)\n"
        "```"
    )
    res = DraftConditionedDecoder.decode_and_condition(raw_output)
    assert "We need to add a check" in res.thought_trace
    assert "def intcomma" in res.repaired_code
    assert res.is_ast_valid is True
    assert len(res.repaired_issues) == 0


def test_dccd_repairs_missing_colon():
    raw_output = (
        "```python\n"
        "def compute_total(a, b)\n"
        "    if a > 0\n"
        "        return a + b\n"
        "    return b\n"
        "```"
    )
    res = DraftConditionedDecoder.decode_and_condition(raw_output)
    assert res.is_ast_valid is True
    assert "def compute_total(a, b):" in res.repaired_code
    assert "if a > 0:" in res.repaired_code
    assert len(res.repaired_issues) >= 2


def test_dccd_balances_unclosed_parenthesis():
    raw_output = (
        "```python\n"
        "def run_check():\n"
        "    values = [1, 2, 3\n"
        "```"
    )
    res = DraftConditionedDecoder.decode_and_condition(raw_output)
    assert "values = [1, 2, 3]" in res.repaired_code
    assert res.is_ast_valid is True
    assert any("closing brackets" in issue for issue in res.repaired_issues)


def test_dccd_to_dict():
    block = DecodedCodeBlock("thought", "raw", "rep", True, ["issue1"], None)
    d = block.to_dict()
    assert d["thought_trace"] == "thought"
    assert d["is_ast_valid"] is True
    assert len(d["repaired_issues"]) == 1
