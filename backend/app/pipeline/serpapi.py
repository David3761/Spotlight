"""SerpApi requests (free plan, about 250 searches a month), retried on network errors and cached per day."""

import json
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app import cache
from app.config import get_settings

SERPAPI_URL = "https://serpapi.com/search.json"
"""The SerpApi search endpoint."""

SERPAPI_TIMEOUT_SECONDS = 25
"""How long one SerpApi search may take."""


class SerpApiError(Exception):
    """Raised when SerpApi refuses a search or returns an error instead of results."""


@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=4),
    reraise=True,
)
async def send_search(params: dict[str, str | int]) -> httpx.Response:
    """Sends one SerpApi search, retrying network errors with exponential backoff."""
    async with httpx.AsyncClient(timeout=SERPAPI_TIMEOUT_SECONDS) as client:
        return await client.get(SERPAPI_URL, params={**params, "api_key": get_settings().serpapi_api_key})


async def serpapi_search(params: dict[str, str | int]) -> dict[str, Any]:
    """Returns a SerpApi result; the same search on the same day is answered from the cache, so it costs no quota.

    Raises `SerpApiError` when SerpApi fails or reports an error.
    """
    today = datetime.now(UTC).date().isoformat()
    key = ["serpapi", today, json.dumps(params, sort_keys=True)]
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        response = await send_search(params)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SerpApiError(str(error)) from error
    if data.get("error"):
        raise SerpApiError(str(data["error"]))
    cache.set(key, data)
    return data
