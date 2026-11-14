"""Gemini calls, rate-limited, retried and cached: JSON and text on the free-tier key, grounded answers on Google Cloud."""

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

GroundingTool = Literal["maps", "search"]
"""What a grounded call looks things up in: Google Maps (live test) or Google Search (mentions)."""

MAPS_TITLE_SUFFIX = " - Google Maps"
"""The suffix Google adds to the titles of Maps sources."""

REQUEST_OPTIONS = types.HttpOptions(timeout=45_000, retry_options=types.HttpRetryOptions(attempts=1))
"""Per-request limits: a 45 s timeout and no SDK retries, so `generate`'s own three tries are the only ones."""

gemini_slots = asyncio.Semaphore(6)
"""The limit on concurrent Gemini calls across the whole backend."""


@lru_cache
def get_client() -> genai.Client:
    """Returns the client on the free-tier `GEMINI_API_KEY`."""
    return genai.Client(api_key=get_settings().gemini_api_key)


@lru_cache
def get_grounded_client() -> genai.Client:
    """Returns the Google Cloud (Vertex AI) client, signed in with the machine's Application Default Credentials."""
    settings = get_settings()
    return genai.Client(vertexai=True, project=settings.google_cloud_project, location=settings.google_cloud_location)


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
async def generate(
    client: genai.Client, model: str, prompt: str, config: types.GenerateContentConfig
) -> types.GenerateContentResponse:
    """Returns one generation with text, within the concurrency limit and with exponential backoff."""
    request_config = config.model_copy(update={"http_options": REQUEST_OPTIONS})
    async with gemini_slots:
        response = await client.aio.models.generate_content(model=model, contents=prompt, config=request_config)
    if not response.text:
        raise ValueError(f"Gemini returned no text (model {model})")
    return response


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
    response = await generate(get_client(), model, prompt, config)
    value = schema.model_validate_json(response.text or "")
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
    text = (await generate(get_client(), model, prompt, config)).text or ""
    cache.set(key, text)
    return text


class GroundingSource(BaseModel):
    """A source a grounded answer cites: a place on Google Maps or a web page."""

    kind: Literal["maps", "web"]
    title: str
    uri: str
    place_id: str | None


class GroundedAnswer(BaseModel):
    """The text of a grounded answer and the sources it cites, in order."""

    text: str
    sources: list[GroundingSource]


async def grounded_call(
    question: str, tool: GroundingTool, lat: float | None = None, lng: float | None = None, run: int = 0
) -> GroundedAnswer:
    """Returns Gemini's grounded answer to a customer's question, sent alone: no system prompt, no business context.

    `run` tells repeated asks of the same question apart, so each run is cached separately.
    """
    model = get_settings().gemini_model_live
    key = ["grounded_call", model, tool, question, str(lat), str(lng), str(run)]
    cached = cache.get(key)
    if cached is not None:
        return GroundedAnswer.model_validate(cached)
    grounding = types.Tool(google_maps=types.GoogleMaps()) if tool == "maps" else types.Tool(google_search=types.GoogleSearch())
    location = None
    if lat is not None and lng is not None:
        location = types.ToolConfig(
            retrieval_config=types.RetrievalConfig(lat_lng=types.LatLng(latitude=lat, longitude=lng), language_code="ro-RO")
        )
    config = types.GenerateContentConfig(tools=[grounding], tool_config=location)
    response = await generate(get_grounded_client(), model, question, config)
    answer = GroundedAnswer(text=response.text or "", sources=get_sources(response))
    cache.set(key, answer.model_dump(mode="json"))
    return answer


def get_sources(response: types.GenerateContentResponse) -> list[GroundingSource]:
    """Returns the Maps places and web pages a grounded response cites."""
    metadata = response.candidates[0].grounding_metadata if response.candidates else None
    sources: list[GroundingSource] = []
    for chunk in (metadata.grounding_chunks or []) if metadata else []:
        if chunk.maps and chunk.maps.uri:
            title = (chunk.maps.title or "").removesuffix(MAPS_TITLE_SUFFIX)
            place_id = (chunk.maps.place_id or "").removeprefix("places/") or None
            sources.append(GroundingSource(kind="maps", title=title, uri=chunk.maps.uri, place_id=place_id))
        elif chunk.web and chunk.web.uri:
            sources.append(GroundingSource(kind="web", title=chunk.web.title or "", uri=chunk.web.uri, place_id=None))
    return sources
