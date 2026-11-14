"""Retrying outside services, and answering from the cache when one is down."""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app import cache

logger = logging.getLogger(__name__)

SERVER_ERROR_STATUSES = frozenset({500, 502, 503, 504})
"""Server errors, which usually pass on a second try."""

RETRYABLE_STATUSES = SERVER_ERROR_STATUSES | {429}
"""Server errors and rate limits, for services whose 429 is a short burst limit rather than a used-up quota."""


def check_status(response: httpx.Response, statuses: frozenset[int]) -> None:
    """Raises for an answer whose status is in `statuses`, so the retry policy tries again."""
    if response.status_code in statuses:
        raise httpx.HTTPStatusError(f"Status {response.status_code}", request=response.request, response=response)


def is_unavailable(error: BaseException, statuses: frozenset[int]) -> bool:
    """Returns whether a failed request means the service is down or busy: a network error or one of `statuses`."""
    if isinstance(error, httpx.TransportError):
        return True
    return isinstance(error, httpx.HTTPStatusError) and error.response.status_code in statuses


def get_retrying(statuses: frozenset[int]) -> AsyncRetrying:
    """Returns a policy of three tries with exponential backoff, for network errors and the given statuses."""
    return AsyncRetrying(
        retry=retry_if_exception(lambda error: is_unavailable(error, statuses)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=4),
        reraise=True,
    )


def get_daily_keys(service: str, request: str) -> tuple[list[str], list[str]]:
    """Returns the cache keys of a request: today's answer, and the last answer ever received."""
    return [service, datetime.now(UTC).date().isoformat(), request], [service, "latest", request]


def save_answer(keys: tuple[list[str], list[str]], data: Any) -> None:
    """Caches an answer as today's and as the latest."""
    today_key, latest_key = keys
    cache.set(today_key, data)
    cache.set(latest_key, data)


def get_fallback(keys: tuple[list[str], list[str]], error: BaseException, statuses: frozenset[int]) -> Any | None:
    """Returns the last answer ever cached when the service is down or busy, or `None`.

    Served while offline, it is also saved as today's answer, so later requests that day don't wait through the retries.
    """
    today_key, latest_key = keys
    if not is_unavailable(error, statuses):
        return None
    latest = cache.get(latest_key)
    if latest is None:
        return None
    logger.warning("Service unavailable; answering %s from the last cached response", latest_key[0])
    if isinstance(error, httpx.TransportError):
        cache.set(today_key, latest)
    return latest
