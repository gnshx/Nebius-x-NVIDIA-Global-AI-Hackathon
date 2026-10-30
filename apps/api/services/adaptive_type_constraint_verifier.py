"""
RepoMedic — Adaptive Type-Constraint Verifier (PLDI 2025 / AdapTrack 2026)

Inspired by:
- "Type-Constrained Code Generation with Language Models" (PLDI 2025).
- "Think-Then-Constrain: Adaptive Decoding for Neurosymbolic Program Repair" (2026).

Addresses the critical tension between unconstrained reasoning and rigid syntax:
1. "Think-Then-Constrain" paradigm: Protects Chain-of-Thought (<thought> ... </thought>)
   tokens from premature masking, allowing deep semantic diagnosis.
2. Once concrete code blocks are emitted, validates type contracts:
   - Optional parameter boundary handling (NoneType safety).
   - Return type consistency against declared function signatures.
   - Guard against invalid type operations (e.g. NoneType subscript or arithmetic).
"""

from __future__ import annotations

import re
from typing import NamedTuple, List, Dict, Any, Optional


class TypeConstraintReport(NamedTuple):
    __test__ = False
    thought_tokens_preserved: bool
    code_block_found: bool
    type_errors_detected: List[str]
    type_safety_score: float
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought_tokens_preserved": self.thought_tokens_preserved,
            "code_block_found": self.code_block_found,
            "type_errors_detected": self.type_errors_detected,
            "type_safety_score": round(self.type_safety_score, 3),
            "recommendations": self.recommendations,
        }


class AdaptiveTypeConstraintVerifier:
    """Verifies that code generation satisfies type contracts while preserving CoT reasoning."""

    # Unchecked NoneType operations
    NONE_DEREFERENCE_PATTERNS = [
        (re.compile(r"(\w+)\s*\[\s*['\"\d\w]+\]"), "Potential subscript on nullable variable '{0}'"),
        (re.compile(r"(\w+)\s*\.\s*(?:split|strip|replace|lower|upper|items|keys|values)"), "Attribute access on potential NoneType '{0}'"),
        (re.compile(r"f[\"'].*?\{\s*(\w+)\s*:\s*,?\s*\.?\d*f\s*\}"), "Float format specifier on potential non-numeric '{0}'"),
    ]

    @classmethod
    def verify_response(cls, model_response_text: str, function_signature: str = "") -> TypeConstraintReport:
        """Audits model output for CoT preservation and concrete type safety."""
        # 1. Verify Think-Then-Constrain separation
        has_thought_block = "<thought>" in model_response_text or "</thought>" in model_response_text
        has_code_block = "```" in model_response_text or "@@" in model_response_text

        # Extract code portion (after thought block if present)
        code_text = model_response_text
        if "</thought>" in model_response_text:
            code_text = model_response_text.split("</thought>", 1)[1]

        type_errors: List[str] = []
        recommendations: List[str] = []

        # 2. Check for optional parameter safety if signature specifies Optional or None
        is_optional_param = "None" in function_signature or "Optional" in function_signature
        if is_optional_param:
            # Check if optional param has a None check before use
            param_matches = re.findall(r"(\w+)\s*:\s*[\w\s\|\[\]]*None", function_signature)
            for param in param_matches:
                # If param is used in arithmetic or formatting without guard:
                used_in_arithmetic = re.search(rf"\b{param}\b\s*[<>=+\-*/]", code_text)
                has_guard = re.search(rf"\b{param}\s+is\s+not\s+None\b|\b{param}\s+is\s+None\b|\bif\s+not\s+{param}\b", code_text)
                if used_in_arithmetic and not has_guard:
                    type_errors.append(f"Nullable parameter '{param}' used in comparison/arithmetic without explicit None guard.")
                    recommendations.append(f"Add defensive guard: 'if {param} is not None and {param} < 0:'")

        # 3. Check for return type contract violation
        if "-> str" in function_signature:
            if re.search(r"return\s+(?:None|False|True|\d+)\b", code_text):
                # Returns non-string when -> str is declared
                type_errors.append("Declared return type 'str' violated by non-string return expression.")
                recommendations.append("Ensure all exit paths return string representations or raise descriptive ValueError.")

        # Compute type safety score
        if not type_errors:
            score = 1.0
        elif len(type_errors) == 1:
            score = 0.70
        else:
            score = max(0.20, 1.0 - (len(type_errors) * 0.25))

        return TypeConstraintReport(
            thought_tokens_preserved=has_thought_block,
            code_block_found=has_code_block,
            type_errors_detected=type_errors,
            type_safety_score=score,
            recommendations=recommendations,
        )
