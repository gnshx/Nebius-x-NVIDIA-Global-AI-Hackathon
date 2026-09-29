"""
RepoMedic — Nebius Token Factory Model Client

Provides ModelClient (OpenAI-compatible) and ModelProvider
with three configurable model slots: planner, coder, fast.

NEVER hard-code model names. Always use settings.
"""
from __future__ import annotations

import json
from typing import Any, Type, TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel

from config import settings

logger = structlog.get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class Message(BaseModel):
    role: str  # system | user | assistant
    content: str


class ModelClient:
    """Async wrapper around Nebius OpenAI-compatible endpoint."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = AsyncOpenAI(
            api_key=settings.nebius_api_key.get_secret_value(),
            base_url=settings.nebius_base_url,
        )

    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a text response."""
        logger.debug("model_generate", model=self.model, messages_count=len(messages))
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

    async def generate_structured(
        self,
        messages: list[Message],
        schema: Type[T],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> T:
        """Generate a response and parse into a Pydantic model."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_suffix = Message(
            role="system",
            content=(
                f"You MUST respond with valid JSON matching this schema:\n"
                f"```json\n{schema_json}\n```\n"
                "Respond ONLY with JSON, no markdown, no explanation."
            ),
        )
        all_messages = [system_suffix] + messages
        raw = await self.generate(all_messages, temperature=temperature, max_tokens=max_tokens)

        # Strip potential markdown code fences
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]

        return schema.model_validate_json(raw.strip())

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a text chunk."""
        response = await self._client.embeddings.create(
            model=settings.nebius_embedding_model,
            input=text,
        )
        return response.data[0].embedding


class ModelProvider:
    """
    Three configurable model slots — set via environment variables.

    planner: NEMOTRON_PLANNER_MODEL  → complex reasoning, planning, review
    coder:   NEMOTRON_CODER_MODEL    → code generation, patches, tests
    fast:    NEMOTRON_FAST_MODEL     → classification, ranking, summarization
    """

    def __init__(self) -> None:
        self.planner = ModelClient(settings.nemotron_planner_model)
        self.coder = ModelClient(settings.nemotron_coder_model)
        self.fast = ModelClient(settings.nemotron_fast_model)


# Singleton
model_provider = ModelProvider()
