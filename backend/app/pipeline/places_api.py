"""Google Places API (New) requests, retried on network errors, rate limits and server errors, and cached per day."""

import json
from typing import Any, Literal

import httpx

from app import cache
from app.config import get_settings
from app.errors import ApiError
from app.pipeline.retry import RETRYABLE_STATUSES, check_status, get_daily_keys, get_fallback, get_retrying, save_answer

PLACES_URL = "https://places.googleapis.com/v1"
"""The base URL of Places API (New)."""

LANGUAGE = {"languageCode": "ro", "regionCode": "RO"}
"""The language and region every request asks for, so labels and hours come in Romanian."""

PLACES_TIMEOUT_SECONDS = 10
"""How long one Places request may take."""


async def send_request(method: Literal["GET", "POST"], path: str, field_mask: str, body: dict[str, Any] | None) -> httpx.Response:
    """Sends one Places request, retrying network errors, rate limits and server errors with exponential backoff."""
    async for attempt in get_retrying(RETRYABLE_STATUSES):
        with attempt:
            async with httpx.AsyncClient(timeout=PLACES_TIMEOUT_SECONDS) as client:
                response = await client.request(
                    method,
                    f"{PLACES_URL}/{path}",
                    headers={"X-Goog-Api-Key": get_settings().places_api_key, "X-Goog-FieldMask": field_mask},
                    params=LANGUAGE if method == "GET" else None,
                    json={**LANGUAGE, **(body or {})} if method == "POST" else None,
                )
            check_status(response, RETRYABLE_STATUSES)
    return response


async def places_request(
    method: Literal["GET", "POST"], path: str, field_mask: str, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Returns a Places response; the same request on the same day is answered from the cache.

    When Places is down or busy (network error, rate limit, server error), the last answer ever received for the same
    request is used, so a rehearsed demo works offline on a later day. Raises `ApiError("upstream_error")` otherwise.
    """
    keys = get_daily_keys("places", json.dumps([method, path, field_mask, body or {}], sort_keys=True))
    cached = cache.get(keys[0])
    if cached is not None:
        return cached
    try:
        response = await send_request(method, path, field_mask, body)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        fallback = get_fallback(keys, error, RETRYABLE_STATUSES)
        if fallback is not None:
            return fallback
        raise ApiError("upstream_error", "Nu am putut căuta pe Google acum. Încearcă din nou.") from error
    save_answer(keys, data)
    return data
