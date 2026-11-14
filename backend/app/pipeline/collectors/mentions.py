"""3.5 Mentions → `mentiuni`: other sites that talk about the business, found by Search-grounded Gemini (M01, M02, M03, M05).

Titles and domains only: no page is read.
"""

import asyncio
import logging
from typing import Literal

import httpx
from pydantic import BaseModel

from app import cache
from app.llm.client import PROMPTS_DIR, GroundedAnswer, grounded_call, json_call
from app.models import ScanInputs
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.collectors.listings import PLATFORM_HOSTS
from app.pipeline.collectors.website import get_website_url
from app.pipeline.fetch import USER_AGENT, check_public_request
from app.pipeline.normalize import get_domain, is_on_host
from app.pipeline.romanian import TYPE_NOUNS, get_list_phrase
from app.pipeline.scoring import CATALOG, get_check_result
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

MENTION_CHECK_IDS = ["M01", "M02", "M03", "M05"]
"""The mention checks (M04 is dropped: it needs page dates)."""

SKIPPED_HOSTS = (
    "google.",
    "instagram.com",
    "facebook.com",
    "tiktok.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    *PLATFORM_HOSTS.values(),
)
"""Hosts that aren't mentions: Google, social profiles and the listing platforms (3.4); a trailing dot takes any ending."""

REDIRECT_TIMEOUT_SECONDS = 5
"""How long following a source's redirect to its real address may take."""

ANSWER_TEXT_LIMIT = 1500
"""How much of each grounded answer the classification reads."""

DOMAIN_COUNT_POINTS = [(6, 45), (3, 30), (1, 15)]
"""M01's points by the lowest number of mentioning domains they apply to."""

MentionType = Literal["news", "blog", "list", "forum", "other"]
"""What kind of page a mention is on."""


class MentionCandidate(BaseModel):
    """A page a grounded answer cited, with the search that found it."""

    domain: str
    url: str | None
    query: str


class MentionVerdict(BaseModel):
    """The L4 classification of one cited page."""

    index: int
    mentions_business: bool
    type: MentionType


class MentionVerdicts(BaseModel):
    """The L4 classifications of every cited page."""

    verdicts: list[MentionVerdict]


async def collect_mentions(inputs: ScanInputs, canonical: CanonicalProfile | None) -> list[CheckResult]:
    """Returns M01, M02, M03 and M05 from the pages Gemini cites for five searches about the business and its area."""
    name = canonical.name if canonical else inputs.business_name
    website = get_website_url(inputs, canonical)
    queries = get_queries(name, inputs)
    answers = await asyncio.gather(*(grounded_call(query, "search") for query in queries))
    candidates = await get_candidates(queries, answers, get_domain(website) if website else None)
    verdicts = await get_verdicts(inputs, name, queries, answers, candidates) if candidates else []
    mentions = [
        (candidates[verdict.index], verdict)
        for verdict in verdicts
        if verdict.mentions_business and 0 <= verdict.index < len(candidates)
    ]
    return [
        get_domains_check(list(dict.fromkeys(candidate.domain for candidate, _ in mentions))),
        get_type_check("M02", "list", mentions),
        get_type_check("M03", "news", mentions),
        get_type_check("M05", "forum", mentions),
    ]


def get_queries(name: str, inputs: ScanInputs) -> list[str]:
    """Returns the five searches: the business by name, and the best businesses of its type around it."""
    plural = TYPE_NOUNS[inputs.business_type].plural
    return [
        f'"{name}" {inputs.city}',
        f'"{name}" {inputs.neighborhood}',
        f"cele mai bune {plural} {inputs.neighborhood}",
        f"top {plural} {inputs.city}",
        f'"{name}" recenzie',
    ]


async def get_candidates(queries: list[str], answers: list[GroundedAnswer], own_domain: str | None) -> list[MentionCandidate]:
    """Returns the cited web pages that could be mentions, once each: not the business's own site, Google, social or listings."""
    cited = [
        (query, source)
        for query, answer in zip(queries, answers, strict=True)
        for source in answer.sources
        if source.kind == "web"
    ]
    urls = await asyncio.gather(*(get_real_url(source.uri) for _, source in cited))
    candidates: dict[str, MentionCandidate] = {}
    for (query, source), url in zip(cited, urls, strict=True):
        domain = get_domain(url) if url else source.title.lower().removeprefix("www.")
        is_own = own_domain is not None and is_on_host(domain, own_domain)
        is_skipped = is_own or any(is_on_host(domain, host) for host in SKIPPED_HOSTS)
        if domain and not is_skipped:
            candidates.setdefault(url or f"{domain} {query}", MentionCandidate(domain=domain, url=url, query=query))
    return list(candidates.values())


async def get_real_url(uri: str) -> str | None:
    """Returns where a grounding redirect leads, following it without reading the page, or `None` when it fails; cached."""
    key = ["grounding_redirect", uri]
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        async with (
            httpx.AsyncClient(
                follow_redirects=True, timeout=REDIRECT_TIMEOUT_SECONDS, event_hooks={"request": [check_public_request]}
            ) as client,
            client.stream("GET", uri, headers={"User-Agent": USER_AGENT}) as response,
        ):
            url = str(response.url)
    except (httpx.HTTPError, httpx.InvalidURL, ValueError):
        logger.info("Following %s failed", uri, exc_info=True)
        return None
    cache.set(key, url)
    return url


async def get_verdicts(
    inputs: ScanInputs, name: str, queries: list[str], answers: list[GroundedAnswer], candidates: list[MentionCandidate]
) -> list[MentionVerdict]:
    """Returns the L4 classification of every candidate page, in one call, with each search's answer as context."""
    sections = []
    for query, answer in zip(queries, answers, strict=True):
        pages = [
            f"- [{index}] {candidate.domain} — {candidate.url or 'adresă necunoscută'}"
            for index, candidate in enumerate(candidates)
            if candidate.query == query
        ]
        if pages:
            sections.append(f"### „{query}”\n\nAnswer:\n{answer.text[:ANSWER_TEXT_LIMIT]}\n\nPages:\n" + "\n".join(pages))
    prompt = (
        (PROMPTS_DIR / "mention_classify.md")
        .read_text(encoding="utf-8")
        .format(
            name=name,
            type_label=inputs.business_type_label_ro.lower(),
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            searches="\n\n".join(sections),
        )
    )
    return (await json_call(prompt, MentionVerdicts)).verdicts


def get_domains_check(domains: list[str]) -> CheckResult:
    """Returns M01: how many other sites mention the business, 0 / 1–2 / 3–5 / 6+ for 0 / 15 / 30 / 45 points."""
    points = next((points for minimum, points in DOMAIN_COUNT_POINTS if len(domains) >= minimum), 0)
    maximum = CATALOG["M01"].points
    status = "pass" if points == maximum else "fail" if points == 0 else "partial"
    found = (
        f"Am găsit mențiuni pe {get_list_phrase(domains)}."
        if domains
        else "Nu am găsit alte site-uri care să vorbească despre tine."
    )
    return get_check_result("M01", status, Evidence(found=found), earned_share=points / maximum)


def get_type_check(
    check_id: str, mention_type: MentionType, mentions: list[tuple[MentionCandidate, MentionVerdict]]
) -> CheckResult:
    """Returns a check passed by one mention of the given kind: a top list (M02), the press (M03) or a forum (M05)."""
    match = next((candidate for candidate, verdict in mentions if verdict.type == mention_type), None)
    if match is None:
        return get_check_result(check_id, "fail")
    return get_check_result(check_id, "pass", Evidence(found=match.domain, url=match.url))
