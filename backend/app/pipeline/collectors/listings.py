"""3.4 Listings → `info`: whether the business is on the platforms that fit it (L01) and whether they agree with Google (L02).

Only links the owner gave or the website shows are read; missing platforms are never searched for.
"""

import asyncio
import logging
from typing import Literal, NamedTuple
from urllib.parse import urlparse

from pydantic import BaseModel

from app.llm.client import PROMPTS_DIR, json_call
from app.models import BusinessType, Platform, ScanInputs
from app.pipeline.assemble import PLATFORM_LABELS
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.collectors.social import get_business_instagram_handle
from app.pipeline.collectors.website import get_expected_terms
from app.pipeline.fetch import fetch_page, is_empty_shell
from app.pipeline.normalize import (
    addresses_match,
    get_domain,
    get_hours_mismatch_days,
    is_on_host,
    names_overlap,
    normalize_phone,
    parse_hours,
)
from app.pipeline.romanian import get_list_phrase
from app.pipeline.scoring import CATALOG, get_check_result
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

LISTING_CHECK_IDS = ["L01", "L02"]
"""The listing checks; L02 is reported per compared field as „L02:<source>:<field>”."""

PLATFORM_HOSTS: dict[Platform, str] = {
    "tripadvisor": "tripadvisor.",
    "glovo": "glovoapp.com",
    "wolt": "wolt.com",
    "bolt_food": "food.bolt.eu",
    "booking": "booking.com",
    "booksy": "booksy.com",
}
"""The host of each platform's pages; a trailing dot stands for any country ending."""

REVIEW_PLATFORMS: dict[BusinessType, list[Platform]] = {
    "cafenea": ["tripadvisor"],
    "restaurant": ["tripadvisor"],
    "bar": ["tripadvisor"],
    "salon": ["booksy"],
    "hotel": ["booking"],
    "magazin": [],
    "altceva": [],
}
"""The platforms besides Instagram that fit each business type."""

DELIVERY_PLATFORMS: list[Platform] = ["glovo", "wolt", "bolt_food"]
"""The delivery platforms expected from a food business that delivers."""

FOOD_TYPES: set[BusinessType] = {"cafenea", "restaurant", "bar"}
"""The business types that can be on delivery platforms."""

INSTAGRAM_LABEL = "Instagram"
"""The display name of Instagram in the platform list."""

LISTING_TEXT_LIMIT = 6000
"""How much of a platform page's text the extraction reads."""

EXTRACTION_TIMEOUT_SECONDS = 20
"""The time limit of one platform page's extraction."""

CONSISTENCY_TIMEOUT_SECONDS = 25
"""The time limit of reading the platform pages for L02, so a slow page never costs L01."""

ListingField = Literal["name", "address", "phone", "hours"]
"""A contact detail compared between a source and Google."""


class ListingExtraction(BaseModel):
    """What the L3 extraction reads from a platform page."""

    is_business_page: bool
    name: str | None
    address: str | None
    phone: str | None
    hours: str | None


class ListingSource(NamedTuple):
    """A platform page that states the business's contact details."""

    platform: Platform
    url: str
    details: ListingExtraction


class FieldComparison(NamedTuple):
    """One contact detail of a source compared with Google's."""

    field: ListingField
    found: str
    expected: str
    matches: bool


async def collect_listings(inputs: ScanInputs, canonical: CanonicalProfile | None, site_links: list[str]) -> list[CheckResult]:
    """Returns L01 from the owner's answers and the website's links, and L02 from the platform pages the website links to."""
    platform_links = get_platform_links(site_links)
    coverage = get_coverage_check(inputs, canonical, site_links, platform_links)
    try:
        consistency = await asyncio.wait_for(
            get_consistency_checks(inputs, canonical, platform_links), CONSISTENCY_TIMEOUT_SECONDS
        )
    except Exception:
        logger.exception("Listing consistency failed or timed out")
        consistency = [get_check_result("L02", "unknown", reason_ro="Nu am putut citi acum paginile de pe alte platforme.")]
    return [coverage, *consistency]


def get_platform_links(links: list[str]) -> dict[Platform, str]:
    """Returns the first link to a page on each platform; links to a platform's home page don't count."""
    platform_links: dict[Platform, str] = {}
    for link in links:
        domain = get_domain(link)
        platform = next((platform for platform, host in PLATFORM_HOSTS.items() if is_on_host(domain, host)), None)
        if platform and platform not in platform_links and urlparse(link).path.strip("/"):
            platform_links[platform] = link
    return platform_links


def get_expected_platforms(business_type: BusinessType, canonical: CanonicalProfile | None) -> list[Platform]:
    """Returns the platforms besides Instagram that fit the business: its review platform, plus delivery if it delivers."""
    delivers = canonical is not None and canonical.attributes.get("delivery", False)
    return REVIEW_PLATFORMS[business_type] + (DELIVERY_PLATFORMS if delivers and business_type in FOOD_TYPES else [])


def get_coverage_check(
    inputs: ScanInputs, canonical: CanonicalProfile | None, site_links: list[str], platform_links: dict[Platform, str]
) -> CheckResult:
    """Returns L01: the share of fitting platforms the business is on, from the owner's answers and the website's links."""
    expected = [INSTAGRAM_LABEL] + [
        PLATFORM_LABELS[platform] for platform in get_expected_platforms(inputs.business_type, canonical)
    ]
    present = {PLATFORM_LABELS[platform] for platform in [*(inputs.platforms or []), *platform_links]}
    if get_business_instagram_handle(inputs, site_links):
        present.add(INSTAGRAM_LABEL)
    missing = [label for label in expected if label not in present]
    present_count = len(expected) - len(missing)
    status = "pass" if not missing else "fail" if present_count == 0 else "partial"
    params = {"missing": get_list_phrase(missing), "present": str(present_count), "expected": str(len(expected))}
    return get_check_result("L01", status, params=params, earned_share=present_count / len(expected))


async def get_consistency_checks(
    inputs: ScanInputs, canonical: CanonicalProfile | None, platform_links: dict[Platform, str]
) -> list[CheckResult]:
    """Returns one L02 check per detail a platform page shares with Google; L02's points are split evenly among them."""
    if canonical is None:
        return [get_check_result("L02", "unknown", reason_ro="Fără Profil Google nu avem cu ce compara datele.")]
    extractions = await asyncio.gather(
        *(get_listing_extraction(inputs, canonical, platform, url) for platform, url in platform_links.items())
    )
    sources = [
        ListingSource(platform, url, details)
        for (platform, url), details in zip(platform_links.items(), extractions, strict=True)
        if details is not None and details.is_business_page
    ]
    comparisons = [(source, comparison) for source in sources for comparison in get_field_comparisons(source, canonical)]
    if not comparisons:
        return [get_check_result("L02", "unknown", reason_ro="Nu am găsit pe alte platforme date de comparat cu Google.")]
    points = CATALOG["L02"].points / len(comparisons)
    return [
        get_check_result(
            f"L02:{source.platform}:{comparison.field}",
            "pass" if comparison.matches else "fail",
            Evidence(found=comparison.found, expected=comparison.expected, url=source.url),
            {"source": PLATFORM_LABELS[source.platform]},
            points_max=points,
        )
        for source, comparison in comparisons
    ]


async def get_listing_extraction(
    inputs: ScanInputs, canonical: CanonicalProfile, platform: Platform, url: str
) -> ListingExtraction | None:
    """Returns the contact details on a platform page, or `None` when it doesn't open, is a login wall or can't be read."""
    page = await fetch_page(url, get_expected_terms(canonical.name, canonical))
    if page is None or page.raw.status >= 400 or is_empty_shell(page.text):
        return None
    prompt = (
        (PROMPTS_DIR / "listing_extract.md")
        .read_text(encoding="utf-8")
        .format(
            platform=PLATFORM_LABELS[platform],
            name=canonical.name,
            type_label=inputs.business_type_label_ro.lower(),
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            url=page.raw.final_url,
            page=page.text[:LISTING_TEXT_LIMIT],
        )
    )
    try:
        return await asyncio.wait_for(json_call(prompt, ListingExtraction), EXTRACTION_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Listing extraction failed for %s", url)
        return None


def get_field_comparisons(source: ListingSource, canonical: CanonicalProfile) -> list[FieldComparison]:
    """Returns the details a source and Google both state, each with whether they match after normalization (§4)."""
    details = source.details
    comparisons: list[FieldComparison] = []
    if details.name:
        comparisons.append(FieldComparison("name", details.name, canonical.name, names_overlap(details.name, canonical.name)))
    if details.address and canonical.formatted_address:
        matches = addresses_match(details.address, canonical.formatted_address)
        comparisons.append(FieldComparison("address", details.address, canonical.formatted_address, matches))
    if details.phone and canonical.phone_e164 and (phone := normalize_phone(details.phone)):
        expected_phone = canonical.national_phone or canonical.phone_e164
        comparisons.append(FieldComparison("phone", details.phone, expected_phone, phone == canonical.phone_e164))
    if details.hours and canonical.has_regular_hours and (hours := parse_hours(details.hours)):
        matches = not get_hours_mismatch_days(hours, canonical.weekly_hours)
        comparisons.append(FieldComparison("hours", details.hours, "; ".join(canonical.hours_ro), matches))
    return comparisons
