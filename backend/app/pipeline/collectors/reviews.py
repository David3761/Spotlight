"""3.2 Reviews → `recenzii`: checks R01–R05 from Google's counts, SerpApi's newest reviews and the onboarding platforms."""

import logging
import statistics
from datetime import UTC, datetime
from typing import Any

from app.models import BusinessType, Platform, ScanInputs
from app.pipeline.assemble import PLATFORM_LABELS
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.collectors.competitors import NearbyCompetitor
from app.pipeline.romanian import TYPE_NOUNS, get_count_phrase
from app.pipeline.scoring import get_check_result, get_unknown_results
from app.pipeline.serpapi import SerpApiError, serpapi_search
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

RECENT_REVIEWS_COUNT = 20
"""How many of the newest reviews SerpApi returns in its one search (R03, R04)."""

GOOD_RATING = 4.6
"""The rating that earns R02 in full."""

FAIR_RATING = 4.3
"""The rating that earns half of R02."""

RECENT_DAYS = 30
"""How new the newest review must be for R03 in full."""

FAIRLY_RECENT_DAYS = 90
"""How new the newest review must be for half of R03."""

GOOD_REPLY_SHARE = 0.8
"""The share of answered recent reviews that earns R04 in full."""

FAIR_REPLY_SHARE = 0.4
"""The share of answered recent reviews that earns half of R04."""

EXPECTED_PLATFORM: dict[BusinessType, Platform] = {
    "cafenea": "tripadvisor",
    "restaurant": "tripadvisor",
    "bar": "tripadvisor",
    "hotel": "booking",
    "salon": "booksy",
}
"""The second review platform R05 expects for each type; other types have no R05."""

GOOGLE_REVIEW_CHECK_IDS = ["R01", "R02", "R03", "R04"]
"""The checks that read Google reviews."""


async def collect_reviews(
    inputs: ScanInputs, canonical: CanonicalProfile | None, nearby: list[NearbyCompetitor]
) -> list[CheckResult]:
    """Returns the review checks; without a Google profile only R05 can run."""
    if canonical is None:
        checks = get_unknown_results(GOOGLE_REVIEW_CHECK_IDS, "Fără Profil Google nu există recenzii pe Google.")
    else:
        checks = await get_google_review_checks(inputs, canonical, nearby)
    platform_check = get_second_platform_check(inputs)
    return checks + ([platform_check] if platform_check else [])


async def get_google_review_checks(
    inputs: ScanInputs, canonical: CanonicalProfile, nearby: list[NearbyCompetitor]
) -> list[CheckResult]:
    """Returns R01–R04 for a business with a Google profile."""
    try:
        recent = await get_recent_reviews(canonical.place_id)
    except SerpApiError:
        logger.exception("SerpApi reviews failed")
        recent = None
    return [
        get_count_check(inputs.business_type, canonical, nearby),
        get_rating_check(canonical),
        get_recency_check(canonical, recent),
        get_replies_check(canonical, recent),
    ]


async def get_recent_reviews(place_id: str) -> list[dict[str, Any]]:
    """Returns the newest reviews of a place from SerpApi, newest first, each with `iso_date` and `response` when answered."""
    data = await serpapi_search(
        {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "sort_by": "newestFirst",
            "hl": "ro",
            "num": RECENT_REVIEWS_COUNT,
        }
    )
    return data.get("reviews", [])


def get_count_check(business_type: BusinessType, canonical: CanonicalProfile, nearby: list[NearbyCompetitor]) -> CheckResult:
    """Returns R01: the review count against the median of the nearby competitors."""
    counts = [competitor.review_count for competitor in nearby if competitor.review_count is not None]
    if not counts:
        reason = f"Nu am găsit {TYPE_NOUNS[business_type].plural} în apropiere cu care să te comparăm."
        return get_check_result("R01", "unknown", reason_ro=reason)
    median = statistics.median(counts)
    count = canonical.review_count or 0
    status = "pass" if count >= median else "partial" if count >= median / 2 else "fail"
    params = {"reviews": get_count_phrase(count, "recenzie", "recenzii"), "median": str(round(median))}
    evidence = Evidence(found=str(count), expected=str(round(median)), url=canonical.google_maps_uri)
    return get_check_result("R01", status, evidence, params)


def get_rating_check(canonical: CanonicalProfile) -> CheckResult:
    """Returns R02: the average rating."""
    if canonical.rating is None:
        return get_check_result("R02", "unknown", reason_ro="Nu ai încă o notă pe Google.")
    rating = canonical.rating
    status = "pass" if rating >= GOOD_RATING else "partial" if rating >= FAIR_RATING else "fail"
    params = {"rating": f"{rating:.1f}".replace(".", ",")}
    return get_check_result(
        "R02", status, Evidence(found=str(rating), expected=str(GOOD_RATING), url=canonical.google_maps_uri), params
    )


def get_recency_check(canonical: CanonicalProfile, recent: list[dict[str, Any]] | None) -> CheckResult:
    """Returns R03: how new the newest review is, from SerpApi or, when it failed, the five reviews Places returns."""
    dates = [review["iso_date"] for review in recent or [] if review.get("iso_date")]
    if recent is None:
        dates = [review.publish_time for review in canonical.reviews if review.publish_time]
    if not dates:
        return get_check_result("R03", "unknown", reason_ro="Nu am găsit recenzii cu dată.")
    newest = max(datetime.fromisoformat(date.replace("Z", "+00:00")) for date in dates)
    days = (datetime.now(UTC) - newest).days
    status = "pass" if days <= RECENT_DAYS else "partial" if days <= FAIRLY_RECENT_DAYS else "fail"
    params = {"days": get_count_phrase(days, "zi", "zile")}
    return get_check_result("R03", status, Evidence(found=newest.date().isoformat(), url=canonical.google_maps_uri), params)


def get_replies_check(canonical: CanonicalProfile, recent: list[dict[str, Any]] | None) -> CheckResult:
    """Returns R04: the share of the newest reviews the owner answered."""
    if recent is None:
        return get_check_result("R04", "unknown", reason_ro="Nu am putut citi acum recenziile recente.")
    if not recent:
        return get_check_result("R04", "unknown", reason_ro="Nu ai încă recenzii la care să răspunzi.")
    answered = sum(1 for review in recent if review.get("response"))
    share = answered / len(recent)
    status = "pass" if share >= GOOD_REPLY_SHARE else "partial" if share >= FAIR_REPLY_SHARE else "fail"
    params = {"unanswered": str(len(recent) - answered), "recent": get_count_phrase(len(recent), "recenzie", "recenzii")}
    evidence = Evidence(found=f"{answered}/{len(recent)}", expected=f"{GOOD_REPLY_SHARE:.0%}", url=canonical.google_maps_uri)
    return get_check_result("R04", status, evidence, params)


def get_second_platform_check(inputs: ScanInputs) -> CheckResult | None:
    """Returns R05: whether the owner is on the review platform expected for the type; `None` for types without one."""
    expected = EXPECTED_PLATFORM.get(inputs.business_type)
    if expected is None:
        return None
    params = {"platform": PLATFORM_LABELS[expected]}
    if inputs.platforms is None:
        return get_check_result("R05", "unknown", params=params, reason_ro="Ai sărit întrebarea despre alte platforme.")
    status = "pass" if expected in inputs.platforms else "fail"
    return get_check_result("R05", status, Evidence(found=", ".join(inputs.platforms), expected=expected), params)
