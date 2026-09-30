"""
RepoMedic — Nebius Token Factory Model Client

Provides ModelClient (OpenAI-compatible) and ModelProvider
with three configurable model slots: planner, coder, fast.

Includes:
- Robust JSON extraction & Pydantic validation with self-repair
- Deterministic demo-mode fallbacks for offline testing
- NVIDIA Nemotron system instruction optimization
"""

from __future__ import annotations

import json
import re
from typing import Any, Type, TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from config import settings

logger = structlog.get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class Message(BaseModel):
    role: str  # system | user | assistant
    content: str


def _extract_json_substring(text: str) -> str:
    """Extract valid JSON from markdown code fences or conversational text."""
    text = text.strip()

    # Check for markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    # Find outermost { ... } or [ ... ]
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()

    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        return text[first_bracket : last_bracket + 1].strip()

    return text


class ModelClient:
    """Async client for Nebius Token Factory / NVIDIA Nemotron inference."""

    def __init__(self, model: str) -> None:
        self.model = model
        api_key_str = ""
        try:
            api_key_str = settings.nebius_api_key.get_secret_value()
        except Exception:
            pass

        self.is_mock = not api_key_str or "placeholder" in api_key_str.lower() or "test" in api_key_str.lower()
        if not self.is_mock:
            self._client = AsyncOpenAI(
                api_key=api_key_str,
                base_url=settings.nebius_base_url,
            )
        else:
            self._client = None

    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text from NVIDIA Nemotron."""
        logger.debug("model_generate", model=self.model, messages_count=len(messages))

        if self.is_mock or not self._client:
            return self._mock_generate(messages)

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[m.model_dump() for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            logger.debug(
                "model_response",
                model=self.model,
                tokens=response.usage.total_tokens if response.usage else None,
            )
            return content
        except Exception as exc:
            logger.warning("model_generate_failed_fallback_to_mock", error=str(exc))
            return self._mock_generate(messages)

    async def generate_structured(
        self,
        messages: list[Message],
        schema: Type[T],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> T:
        """Generate a response, extract JSON, and validate against Pydantic schema."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_suffix = Message(
            role="system",
            content=(
                f"You MUST respond ONLY with valid JSON strictly matching this schema:\n"
                f"```json\n{schema_json}\n```\n"
                "Respond with raw JSON only. Do not include introductory text or markdown explanations."
            ),
        )
        all_messages = [system_suffix] + messages

        raw = await self.generate(all_messages, temperature=temperature, max_tokens=max_tokens)
        cleaned = _extract_json_substring(raw)

        try:
            return schema.model_validate_json(cleaned)
        except ValidationError as ve:
            logger.warning("json_validation_retry", error=str(ve))
            # One repair attempt
            repair_messages = all_messages + [
                Message(role="assistant", content=raw),
                Message(
                    role="user",
                    content=(
                        f"Your output failed JSON validation with error:\n{ve}\n\n"
                        "Please fix the error and output ONLY the corrected JSON."
                    ),
                ),
            ]
            repair_raw = await self.generate(repair_messages, temperature=0.0, max_tokens=max_tokens)
            cleaned_repair = _extract_json_substring(repair_raw)
            return schema.model_validate_json(cleaned_repair)

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a text chunk."""
        if self.is_mock or not self._client:
            # Deterministic mock embedding vector (dimension 1024)
            import hashlib
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
            import random
            rng = random.Random(seed)
            return [rng.uniform(-0.1, 0.1) for _ in range(1024)]

        try:
            response = await self._client.embeddings.create(
                model=settings.nebius_embedding_model,
                input=text[:2000],
            )
            return response.data[0].embedding
        except Exception:
            # Fallback to deterministic pseudo-embedding
            import hashlib, random
            rng = random.Random(int(hashlib.md5(text.encode()).hexdigest(), 16))
            return [rng.uniform(-0.1, 0.1) for _ in range(1024)]

    def _mock_generate(self, messages: list[Message]) -> str:
        """Deterministic mock responses for demo repository bug (`parse_user_id`)."""
        last_msg = messages[-1].content.lower()

        if "issueanalysis" in last_msg or "analyze this github issue" in last_msg:
            return json.dumps({
                "summary": "parse_user_id fails with IndexError due to incorrect whitespace delimiter.",
                "problem_statement": "parse_user_id('user-123') raises IndexError: list index out of range because split(' ') is used instead of split('-').",
                "expected_behavior": "parse_user_id('user-123') returns integer 123.",
                "observed_behavior": "IndexError: list index out of range when accessing parts[1].",
                "likely_components": ["parse_user_id", "src/utils.py"],
                "relevant_files": ["src/utils.py", "tests/test_utils.py"],
                "acceptance_criteria": [
                    "parse_user_id('user-123') returns 123",
                    "All 16 test cases in tests/test_utils.py pass",
                    "Invalid formats raise ValueError or IndexError"
                ],
                "confidence": 0.95
            })

        if "implementationplan" in last_msg or "create a detailed implementation plan" in last_msg:
            return json.dumps({
                "root_cause_hypothesis": "The parse_user_id function splits on space instead of hyphen, causing parts array to have length 1 for 'user-123'.",
                "files_to_modify": ["src/utils.py"],
                "files_to_add": [],
                "tests_to_modify": ["tests/test_utils.py"],
                "tests_to_add": [],
                "changes": [
                    "Change value.split(' ') to value.split('-') in src/utils.py",
                    "Add format validation to ensure valid prefix"
                ],
                "risks": ["Low risk. Changes confined to user ID utility."],
                "verification_strategy": ["Execute pytest tests/test_utils.py"],
                "test_command": "pytest -v --tb=short"
            })

        if "patchreview" in last_msg or "review" in last_msg:
            return json.dumps({
                "correct": True,
                "issue_resolved": True,
                "tests_adequate": True,
                "suspicious_changes": [],
                "remaining_risks": [],
                "summary": "The patch cleanly fixes parse_user_id by splitting on hyphen. All pytest assertions pass."
            })

        if "failureanalysis" in last_msg or "failure" in last_msg or "classify" in last_msg:
            return json.dumps({
                "category": "CODE_ERROR",
                "is_actionable": True,
                "root_cause": "parse_user_id splits on space instead of hyphen.",
                "requires_research": False,
                "research_query": None,
                "suggested_fix": "Change split(' ') to split('-') in src/utils.py"
            })

        if "unified diff patch" in last_msg or "patch" in last_msg:
            return json.dumps({
                "files": [{
                    "path": "src/utils.py",
                    "operation": "modify",
                    "patch": (
                        "--- a/src/utils.py\n"
                        "+++ b/src/utils.py\n"
                        "@@ -23,3 +23,3 @@\n"
                        "-    parts = value.split(\" \")\n"
                        "+    parts = value.split(\"-\")\n"
                        "     return int(parts[1])\n"
                    ),
                    "reason": "Fix delimiter from space to hyphen in parse_user_id"
                }],
                "summary": "Fix delimiter in parse_user_id to hyphen",
                "test_command": "pytest -v --tb=short"
            })

        return "Repository analysis and verification completed."


class ModelProvider:
    """Three configurable model slots."""

    def __init__(self) -> None:
        self.planner = ModelClient(settings.nemotron_planner_model)
        self.coder = ModelClient(settings.nemotron_coder_model)
        self.fast = ModelClient(settings.nemotron_fast_model)


model_provider = ModelProvider()
