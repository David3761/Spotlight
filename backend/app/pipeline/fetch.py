"""Fetching web pages the way AI crawlers see them: raw HTML first, a headless browser render only when that's empty."""

import asyncio
import ipaddress
import logging
import socket
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from playwright.async_api import Browser, Playwright, async_playwright
from pydantic import BaseModel
from selectolax.lexbor import LexborHTMLParser

from app import cache
from app.pipeline.normalize import strip_diacritics

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 10
"""How long one raw page fetch may take."""

RENDER_TIMEOUT_SECONDS = 15
"""How long one browser render may take."""

MIN_VISIBLE_CHARACTERS = 200
"""Less visible text than this means the raw HTML is an empty shell."""

EMPTY_SHELL_MARKERS = ("enable javascript", "activeaza javascript", "you need to enable javascript")
"""Phrases of pages that show nothing without JavaScript."""

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/159.0 Safari/537.36"
"""The browser identity pages are fetched with."""

HIDDEN_TAGS = "script, style, noscript, template, svg"
"""Elements whose text a visitor never sees."""


class RawPage(BaseModel):
    """A page as the server sends it, before any JavaScript runs."""

    url: str
    final_url: str
    status: int
    html: str
    elapsed_seconds: float


class FetchedPage(BaseModel):
    """A page with its raw HTML and visible text, plus the rendered text when the raw text looked empty."""

    raw: RawPage
    raw_text: str
    rendered_text: str | None

    @property
    def text(self) -> str:
        """The text a reader gets: the render when there was one, the raw text otherwise."""
        return self.rendered_text or self.raw_text


browser_lock = asyncio.Lock()
"""Keeps two renders from launching two browsers."""

playwright_handle: Playwright | None = None
"""The running Playwright driver, started on the first render."""

shared_browser: Browser | None = None
"""The headless browser reused by every render."""


def get_today() -> str:
    """Returns today's UTC date, the cache key part that makes fetched pages fresh once a day."""
    return datetime.now(UTC).date().isoformat()


async def is_public_host(host: str | None) -> bool:
    """Returns whether a host name resolves only to public internet addresses, so the server never fetches its own network."""
    if not host or host == "localhost" or host.endswith((".local", ".internal")):
        return False
    try:
        addresses = await asyncio.to_thread(socket.getaddrinfo, host, None)
    except OSError:
        return False
    return all(ipaddress.ip_address(address[4][0]).is_global for address in addresses)


async def check_public_request(request: httpx.Request) -> None:
    """Refuses a request, redirects included, whose host isn't on the public internet."""
    if not await is_public_host(request.url.host):
        raise httpx.RequestError(f"Refusing to fetch a non-public host: {request.url.host}", request=request)


async def fetch_raw(url: str) -> RawPage | None:
    """Returns the raw page at a URL after redirects, or `None` when it can't be reached.

    Answers below 400 are cached per day; errors aren't, so a passing outage doesn't stick.
    """
    key = ["raw_page", get_today(), url]
    cached = cache.get(key)
    if cached is not None:
        return RawPage.model_validate(cached)
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=FETCH_TIMEOUT_SECONDS, event_hooks={"request": [check_public_request]}
        ) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
    except (httpx.HTTPError, httpx.InvalidURL, ValueError):
        logger.info("Fetching %s failed", url, exc_info=True)
        return None
    page = RawPage(
        url=url,
        final_url=str(response.url),
        status=response.status_code,
        html=response.text,
        elapsed_seconds=response.elapsed.total_seconds(),
    )
    if page.status < 400:
        cache.set(key, page.model_dump(mode="json"))
    return page


def get_visible_text(html: str) -> str:
    """Returns the text a visitor sees in an HTML page, whitespace collapsed."""
    tree = LexborHTMLParser(html)
    for node in tree.css(HIDDEN_TAGS):
        node.decompose()
    root = tree.body or tree.root
    return " ".join(root.text(separator=" ", strip=True).split()) if root else ""


def is_empty_shell(text: str) -> bool:
    """Returns whether raw text is an empty shell: too short to be content, or asking for JavaScript."""
    normalized = strip_diacritics(text)
    return len(text) < MIN_VISIBLE_CHARACTERS or any(marker in normalized for marker in EMPTY_SHELL_MARKERS)


def looks_empty(text: str, expected_terms: list[str]) -> bool:
    """Returns whether raw text needs a render: an empty shell, or missing every expected term (when there are any)."""
    if is_empty_shell(text):
        return True
    normalized = strip_diacritics(text)
    terms = [strip_diacritics(term) for term in expected_terms if term]
    return bool(terms) and not any(term in normalized for term in terms)


async def get_browser() -> Browser:
    """Returns the shared headless browser, launching it on first use."""
    global playwright_handle, shared_browser
    async with browser_lock:
        if shared_browser is None or not shared_browser.is_connected():
            playwright_handle = playwright_handle or await async_playwright().start()
            shared_browser = await playwright_handle.chromium.launch()
        return shared_browser


async def render_text(url: str) -> str | None:
    """Returns the visible text of a page after its JavaScript runs, or `None` when the render fails; cached per day."""
    key = ["rendered_page", get_today(), url]
    cached = cache.get(key)
    if cached is not None:
        return cached
    if not await is_public_host(urlparse(url).hostname):
        return None
    try:
        browser = await get_browser()
        page = await browser.new_page(user_agent=USER_AGENT)
        try:
            await page.goto(url, wait_until="networkidle", timeout=RENDER_TIMEOUT_SECONDS * 1000)
            text = " ".join((await page.inner_text("body")).split())
        finally:
            await page.close()
    except Exception:
        logger.info("Rendering %s failed", url, exc_info=True)
        return None
    cache.set(key, text)
    return text


async def fetch_page(url: str, expected_terms: list[str]) -> FetchedPage | None:
    """Returns a page's raw HTML and text, rendering it in the browser only when the raw text looks empty.

    `expected_terms` are words the page should contain (the homepage: the business name); pass none for other pages,
    which are rendered only when they are empty shells. Error pages are never rendered.
    """
    raw = await fetch_raw(url)
    if raw is None:
        return None
    raw_text = get_visible_text(raw.html)
    needs_render = raw.status < 400 and looks_empty(raw_text, expected_terms)
    rendered = await render_text(raw.final_url) if needs_render else None
    return FetchedPage(raw=raw, raw_text=raw_text, rendered_text=rendered)


async def close_browser() -> None:
    """Closes the shared browser and the Playwright driver, if they were started."""
    global playwright_handle, shared_browser
    if shared_browser is not None:
        await shared_browser.close()
        shared_browser = None
    if playwright_handle is not None:
        await playwright_handle.stop()
        playwright_handle = None
