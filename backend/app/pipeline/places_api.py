"""Google Places API (New) requests, retried on network errors and cached per day."""

import json
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app import cache
from app.config import get_settings
from app.errors import ApiError

PLACES_URL = "https://places.googleapis.com/v1"
"""The base URL of Places API (New)."""

LANGUAGE = {"languageCode": "ro", "regionCode": "RO"}
"""The language and region every request asks for, so labels and hours come in Romanian."""

PLACES_TIMEOUT_SECONDS = 10
"""How long one Places request may take."""


@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=4),
    reraise=True,
)
async def send_request(method: Literal["GET", "POST"], path: str, field_mask: str, body: dict[str, Any] | None) -> httpx.Response:
    """Sends one Places request, retrying network errors with exponential backoff."""
    async with httpx.AsyncClient(timeout=PLACES_TIMEOUT_SECONDS) as client:
        return await client.request(
            method,
            f"{PLACES_URL}/{path}",
            headers={"X-Goog-Api-Key": get_settings().places_api_key, "X-Goog-FieldMask": field_mask},
            params=LANGUAGE if method == "GET" else None,
            json={**LANGUAGE, **(body or {})} if method == "POST" else None,
        )


async def places_request(
    method: Literal["GET", "POST"], path: str, field_mask: str, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Returns a Places response; the same request on the same day is answered from the cache.

    Raises `ApiError("upstream_error")` when Places refuses or fails.
    """
    today = datetime.now(UTC).date().isoformat()
    key = ["places", today, method, path, field_mask, json.dumps(body or {}, sort_keys=True)]
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        response = await send_request(method, path, field_mask, body)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise ApiError("upstream_error", "Nu am putut căuta pe Google acum. Încearcă din nou.") from error
    cache.set(key, data)
    return data
