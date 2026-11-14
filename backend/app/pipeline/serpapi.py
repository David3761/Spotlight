"""SerpApi requests (free plan, about 250 searches a month), retried on network and server errors, cached per day."""

import json
from typing import Any

import httpx

from app import cache
from app.config import get_settings
from app.pipeline.retry import SERVER_ERROR_STATUSES, check_status, get_daily_keys, get_fallback, get_retrying, save_answer

SERPAPI_URL = "https://serpapi.com/search.json"
"""The SerpApi search endpoint."""

SERPAPI_TIMEOUT_SECONDS = 25
"""How long one SerpApi search may take."""


class SerpApiError(Exception):
    """Raised when SerpApi refuses a search or returns an error instead of results."""


async def send_search(params: dict[str, str | int]) -> httpx.Response:
    """Sends one SerpApi search, retrying network and server errors with exponential backoff (its 429 means the quota is used up)."""
    async for attempt in get_retrying(SERVER_ERROR_STATUSES):
        with attempt:
            async with httpx.AsyncClient(timeout=SERPAPI_TIMEOUT_SECONDS) as client:
                response = await client.get(SERPAPI_URL, params={**params, "api_key": get_settings().serpapi_api_key})
            check_status(response, SERVER_ERROR_STATUSES)
    return response


async def serpapi_search(params: dict[str, str | int]) -> dict[str, Any]:
    """Returns a SerpApi result; the same search on the same day is answered from the cache, so it costs no quota.

    When SerpApi is down (network or server error), the last result ever received for the same search is used.

    Raises `SerpApiError` when SerpApi fails or reports an error.
    """
    keys = get_daily_keys("serpapi", json.dumps(params, sort_keys=True))
    cached = cache.get(keys[0])
    if cached is not None:
        return cached
    try:
        response = await send_search(params)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        fallback = get_fallback(keys, error, SERVER_ERROR_STATUSES)
        if fallback is not None:
            return fallback
        raise SerpApiError(str(error)) from error
    if data.get("error"):
        raise SerpApiError(str(data["error"]))
    save_answer(keys, data)
    return data
