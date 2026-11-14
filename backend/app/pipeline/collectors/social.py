"""3.6 Social → `social`: the Instagram profile, recent posts, cross-links and bio (S02–S05). No Facebook anywhere."""

import asyncio
import logging
import re
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel

from app import cache
from app.config import get_settings
from app.llm.client import PROMPTS_DIR, json_call
from app.models import ScanInputs
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.collectors.website import get_website_url
from app.pipeline.fetch import get_today
from app.pipeline.normalize import get_domain, get_instagram_handle
from app.pipeline.romanian import get_count_phrase, get_list_phrase
from app.pipeline.scoring import get_check_result
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

SOCIAL_CHECK_IDS = ["S02", "S03", "S04", "S05"]
"""The social checks."""

BUSINESS_DISCOVERY_URL = "https://graph.facebook.com/v27.0/{user_id}"
"""The Instagram Graph API node Business Discovery is read through: the app user's own professional account."""

BUSINESS_DISCOVERY_FIELDS = "business_discovery.username({handle}){{biography,website,media_count,media.limit(10){{timestamp}}}}"
"""The Business Discovery fields: the bio, the website link and the dates of the newest posts."""

GRAPH_TIMEOUT_SECONDS = 10
"""How long the Business Discovery request may take."""

HANDLE_PATTERN = re.compile(r"[A-Za-z0-9_.]{1,30}")
"""A valid Instagram username, checked before it goes into the Business Discovery field expression."""

RECENT_POST_DAYS = 30
"""How new the newest post must be for S03."""

BIO_JUDGE_TIMEOUT_SECONDS = 20
"""The time limit of the bio judgement, so a slow Gemini never costs the other social checks."""

NO_PROFILE_READ_RO = "Nu am putut citi descrierea de pe Instagram."
"""Why S05 couldn't run: Business Discovery returned nothing (no token, or not a business or creator account)."""

NO_POSTS_READ_RO = "Nu am putut vedea postările de pe Instagram."
"""Why S03 couldn't run: no posts read and no answer about posting in onboarding."""


class InstagramProfile(BaseModel):
    """What Business Discovery tells about an Instagram business or creator account."""

    biography: str | None
    website: str | None
    newest_post_at: datetime | None


class BioVerdict(BaseModel):
    """The L1 judge's answer on whether an Instagram bio says what the business is and where it is."""

    fits: bool
    reason: str


async def collect_social(inputs: ScanInputs, canonical: CanonicalProfile | None, site_links: list[str]) -> list[CheckResult]:
    """Returns S02–S05 from the Instagram handle the owner gave or the site links to, read through Business Discovery."""
    handle = get_business_instagram_handle(inputs, site_links)
    profile = await get_instagram_profile(handle) if handle else None
    profile_url = f"https://instagram.com/{handle}" if handle else None
    return [
        get_profile_check(handle, profile_url),
        get_posts_check(inputs, profile, profile_url),
        get_cross_links_check(inputs, canonical, site_links, handle, profile),
        await get_bio_check(inputs, canonical, profile, profile_url),
    ]


def get_business_instagram_handle(inputs: ScanInputs, site_links: list[str]) -> str | None:
    """Returns the business's Instagram handle: the one the owner gave, else the first one the website links to."""
    return get_instagram_handle(inputs.instagram_url) or next(
        (handle for link in site_links if "instagram.com" in link and (handle := get_instagram_handle(link))),
        None,
    )


async def get_instagram_profile(handle: str) -> InstagramProfile | None:
    """Returns the account's Business Discovery data, or `None` without a token, for a personal account or on any error.

    Answers are cached per day; failures aren't. The token never reaches the logs: errors log only status and message.
    """
    settings = get_settings()
    if not settings.meta_access_token or not settings.meta_ig_user_id or not HANDLE_PATTERN.fullmatch(handle):
        return None
    key = ["instagram_profile", get_today(), handle.lower()]
    cached = cache.get(key)
    if cached is not None:
        return InstagramProfile.model_validate(cached)
    try:
        async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_SECONDS) as client:
            response = await client.get(
                BUSINESS_DISCOVERY_URL.format(user_id=settings.meta_ig_user_id),
                params={"fields": BUSINESS_DISCOVERY_FIELDS.format(handle=handle), "access_token": settings.meta_access_token},
            )
        data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        logger.info("Business Discovery failed for %s: %s", handle, type(error).__name__)
        return None
    discovery = data.get("business_discovery") if isinstance(data, dict) else None
    if response.status_code != 200 or not isinstance(discovery, dict):
        error = data.get("error") if isinstance(data, dict) else None
        message = error.get("message") if isinstance(error, dict) else None
        logger.info("Business Discovery returned %s for %s: %s", response.status_code, handle, message)
        return None
    timestamps = [post["timestamp"] for post in discovery.get("media", {}).get("data", []) if "timestamp" in post]
    profile = InstagramProfile(
        biography=discovery.get("biography") or None,
        website=discovery.get("website") or None,
        newest_post_at=max((datetime.fromisoformat(timestamp) for timestamp in timestamps), default=None),
    )
    cache.set(key, profile.model_dump(mode="json"))
    return profile


def get_profile_check(handle: str | None, profile_url: str | None) -> CheckResult:
    """Returns S02: an Instagram profile the owner gave or the site links to.

    Instagram answers 200 even for usernames that don't exist, so a link the owner controls is the evidence.
    """
    if handle is None:
        found = "Nu ai dat un link de Instagram și nu am găsit niciunul pe site."
        return get_check_result("S02", "fail", Evidence(found=found))
    return get_check_result("S02", "pass", Evidence(url=profile_url))


def get_posts_check(inputs: ScanInputs, profile: InstagramProfile | None, profile_url: str | None) -> CheckResult:
    """Returns S03: a post in the last 30 days, from the newest Instagram post or, without one read, the owner's answer."""
    if profile is not None:
        if profile.newest_post_at is None:
            return get_check_result("S03", "fail", Evidence(found="Nu ai nicio postare pe Instagram.", url=profile_url))
        days = (datetime.now(UTC) - profile.newest_post_at).days
        found = (
            "Ai postat azi pe Instagram."
            if days == 0
            else f"Ultima postare pe Instagram e de acum {get_count_phrase(days, 'zi', 'zile')}."
        )
        status = "pass" if days <= RECENT_POST_DAYS else "fail"
        return get_check_result("S03", status, Evidence(found=found, url=profile_url))
    answer = inputs.self_report.last_social_post if inputs.self_report else None
    if answer == "luna_asta":
        return get_check_result("S03", "pass", Evidence(found="Ai spus că ai postat luna aceasta."))
    if answer == "mai_demult":
        return get_check_result("S03", "fail", Evidence(found="Ai spus că ultima postare e mai veche de o lună."))
    if answer == "niciodata":
        return get_check_result("S03", "fail", Evidence(found="Ai spus că nu ai postat încă."))
    return get_check_result("S03", "unknown", reason_ro=NO_POSTS_READ_RO)


def get_cross_links_check(
    inputs: ScanInputs,
    canonical: CanonicalProfile | None,
    site_links: list[str],
    handle: str | None,
    profile: InstagramProfile | None,
) -> CheckResult:
    """Returns S04: the site links to Instagram, Instagram links to the site and Google links to the site.

    Without Business Discovery the Instagram → site link can't be read and is left out.
    """
    website = get_website_url(inputs, canonical)
    if website is None:
        return get_check_result("S04", "unknown", reason_ro="Fără site nu sunt linkuri de verificat între site și Instagram.")
    site_domain = get_domain(website)
    links = {
        "linkul către Instagram pe site": handle is not None
        and any((get_instagram_handle(link) or "").lower() == handle.lower() for link in site_links if "instagram.com" in link),
        "linkul către site pe Profilul tău Google": canonical is not None and canonical.website is not None,
    }
    if profile is not None:
        links["linkul către site în descrierea de pe Instagram"] = (
            profile.website is not None and get_domain(profile.website) == site_domain
        )
    missing = [label for label, present in links.items() if not present]
    status = "pass" if not missing else "fail" if len(missing) == len(links) else "partial"
    return get_check_result("S04", status, params={"missing": get_list_phrase(missing)})


async def get_bio_check(
    inputs: ScanInputs, canonical: CanonicalProfile | None, profile: InstagramProfile | None, profile_url: str | None
) -> CheckResult:
    """Returns S05: whether the Instagram bio says what the business is and where, judged by the LLM."""
    if profile is None:
        return get_check_result("S05", "unknown", reason_ro=NO_PROFILE_READ_RO)
    evidence = Evidence(found=profile.biography, url=profile_url)
    if not profile.biography:
        return get_check_result("S05", "fail", evidence)
    prompt = (
        (PROMPTS_DIR / "instagram_bio_judge.md")
        .read_text(encoding="utf-8")
        .format(
            name=canonical.name if canonical else inputs.business_name,
            type_label=inputs.business_type_label_ro.lower(),
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            biography=profile.biography,
        )
    )
    try:
        verdict = await asyncio.wait_for(json_call(prompt, BioVerdict), BIO_JUDGE_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Instagram bio judge failed")
        return get_check_result("S05", "unknown", evidence, reason_ro="Nu am putut verifica acum descrierea de pe Instagram.")
    return get_check_result("S05", "pass" if verdict.fits else "fail", evidence)
