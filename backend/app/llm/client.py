"""Gemini calls on the free-tier key: structured JSON and plain text, rate-limited, retried and cached."""

import asyncio
import json
from functools import lru_cache
from typing import Literal

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app import cache
from app.config import get_settings

Tier = Literal["fast", "smart"]
"""The model tier: `fast` for extraction and judging, `smart` for texts and chat."""

gemini_slots = asyncio.Semaphore(6)
"""The limit on concurrent Gemini calls across the whole backend."""


@lru_cache
def get_client() -> genai.Client:
    """Returns the client on the free-tier `GEMINI_API_KEY`."""
    return genai.Client(api_key=get_settings().gemini_api_key)


def get_model(tier: Tier) -> str:
    """Returns the model ID for a tier, from `.env`."""
    settings = get_settings()
    if tier == "fast":
        return settings.gemini_model_fast
    return settings.gemini_model_smart


def is_retryable(error: BaseException) -> bool:
    """Returns whether a failed call is worth retrying: rate limits, server errors and network errors."""
    if isinstance(error, errors.ServerError | httpx.TransportError):
        return True
    return isinstance(error, errors.ClientError) and error.code == 429


@retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=8),
    reraise=True,
)
async def generate_text(client: genai.Client, model: str, prompt: str, config: types.GenerateContentConfig) -> str:
    """Returns the text of one generation, within the concurrency limit and with exponential backoff."""
    async with gemini_slots:
        response = await client.aio.models.generate_content(model=model, contents=prompt, config=config)
    if not response.text:
        raise ValueError(f"Gemini returned no text (model {model})")
    return response.text


async def json_call[T: BaseModel](prompt: str, schema: type[T], tier: Tier = "fast", system: str | None = None) -> T:
    """Returns Gemini's answer parsed into `schema`; an identical call is answered from the cache."""
    model = get_model(tier)
    json_schema = schema.model_json_schema()
    key = ["json_call", model, system or "", json.dumps(json_schema, sort_keys=True), prompt]
    cached = cache.get(key)
    if cached is not None:
        return schema.model_validate(cached)
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_json_schema=json_schema,
    )
    value = schema.model_validate_json(await generate_text(get_client(), model, prompt, config))
    cache.set(key, value.model_dump(mode="json"))
    return value


async def text_call(prompt: str, tier: Tier = "smart", system: str | None = None) -> str:
    """Returns Gemini's plain-text answer; an identical call is answered from the cache."""
    model = get_model(tier)
    key = ["text_call", model, system or "", prompt]
    cached = cache.get(key)
    if cached is not None:
        return cached
    config = types.GenerateContentConfig(system_instruction=system)
    text = await generate_text(get_client(), model, prompt, config)
    cache.set(key, text)
    return text
