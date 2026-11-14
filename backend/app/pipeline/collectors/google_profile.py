"""3.1 Google profile → `profil`: checks G01–G12 from the canonical profile, a category judgement and self-reports."""

import asyncio
import logging

from pydantic import BaseModel

from app.llm.client import PROMPTS_DIR, json_call
from app.models import BusinessType, PostRecency, ScanInputs, YesNoUnknown
from app.pipeline.canonical import ATTRIBUTE_LABELS_RO, CanonicalProfile
from app.pipeline.romanian import TYPE_NOUNS, get_count_phrase, get_list_phrase
from app.pipeline.scoring import get_check_result
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

CATEGORY_TIMEOUT_SECONDS = 10
"""The time limit of the category judgement, so a slow Gemini never costs the other profile checks."""

MIN_PHOTOS = 5
"""The photo count G05 asks for."""

MIN_PHOTOS_PARTIAL = 3
"""The photo count that earns half of G05."""

SELF_REPORT_UNKNOWN_RO = "Ai răspuns „nu știu” sau ai sărit întrebarea."
"""Why a self-reported check couldn't be scored."""

CLOSED_STATUS_RO = {
    "CLOSED_TEMPORARILY": "Google arată afacerea ca închisă temporar.",
    "CLOSED_PERMANENTLY": "Google arată afacerea ca închisă definitiv.",
}
"""What G01 says when Google shows the business as closed."""

TYPE_ATTRIBUTES: dict[BusinessType, list[str]] = {
    "cafenea": ["dineIn", "takeout", "outdoorSeating", "servesCoffee", "acceptsCreditCards"],
    "restaurant": ["dineIn", "takeout", "delivery", "outdoorSeating", "acceptsCreditCards"],
    "bar": ["dineIn", "outdoorSeating", "goodForGroups", "acceptsCreditCards"],
    "salon": ["acceptsCreditCards", "wheelchairAccessibleEntrance"],
    "hotel": ["acceptsCreditCards", "wheelchairAccessibleEntrance"],
    "magazin": ["acceptsCreditCards", "wheelchairAccessibleEntrance"],
    "altceva": ["acceptsCreditCards", "wheelchairAccessibleEntrance"],
}
"""The attributes G10 expects to be filled in (yes or no) for each business type."""


class CategoryVerdict(BaseModel):
    """The L1 judge's answer on whether Google's main category fits the business."""

    fits: bool
    reason: str


async def collect_google_profile(inputs: ScanInputs, canonical: CanonicalProfile | None) -> list[CheckResult]:
    """Returns the Google profile checks; without an operating profile, G01 alone, so the chapter scores 0."""
    if canonical is None:
        return [get_check_result("G01", "fail", params={"status": "Nu am găsit un Profil Google pentru afacere."})]
    if canonical.business_status in CLOSED_STATUS_RO:
        status_ro = CLOSED_STATUS_RO[canonical.business_status]
        return [get_check_result("G01", "fail", Evidence(found=canonical.business_status), {"status": status_ro})]
    return [
        await get_category_check(inputs, canonical),
        get_regular_hours_check(canonical),
        get_special_hours_check(canonical),
        get_photos_check(canonical),
        get_presence_check("G06", canonical.website, canonical.google_maps_uri),
        get_presence_check("G07", canonical.national_phone, canonical.google_maps_uri),
        get_yes_no_check("G08", inputs.self_report.has_google_description),
        get_recent_post_check(inputs.self_report.last_google_post),
        get_attributes_check(inputs.business_type, canonical),
        get_presence_check("G11", canonical.price_level or canonical.price_range, canonical.google_maps_uri),
        get_yes_no_check("G12", inputs.self_report.profile_claimed),
    ]


async def get_category_check(inputs: ScanInputs, canonical: CanonicalProfile) -> CheckResult:
    """Returns G02: whether Google's main category fits the business, judged by the LLM; `unknown` when it can't answer."""
    params = {"category": canonical.primary_type_label or canonical.primary_type or "necunoscută"}
    evidence = Evidence(found=canonical.primary_type, expected=inputs.business_type, url=canonical.google_maps_uri)
    if canonical.primary_type is None:
        return get_check_result("G02", "fail", evidence, params)
    prompt = (
        (PROMPTS_DIR / "category_judge.md")
        .read_text(encoding="utf-8")
        .format(
            type_label=inputs.business_type_label_ro,
            business_type=TYPE_NOUNS[inputs.business_type].singular,
            primary_type_label=canonical.primary_type_label or canonical.primary_type,
            primary_type=canonical.primary_type,
            types=", ".join(canonical.types),
        )
    )
    try:
        verdict = await asyncio.wait_for(json_call(prompt, CategoryVerdict), CATEGORY_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Category judge failed")
        return get_check_result("G02", "unknown", evidence, params, reason_ro="Nu am putut verifica acum categoria.")
    return get_check_result("G02", "pass" if verdict.fits else "fail", evidence, params)


def get_regular_hours_check(canonical: CanonicalProfile) -> CheckResult:
    """Returns G03: whether the profile has opening hours for the week (Google lists every day once hours are set)."""
    days = len(canonical.hours_ro) if canonical.has_regular_hours else 0
    evidence = Evidence(found=f"{days}/7", expected="7/7", url=canonical.google_maps_uri)
    return get_check_result("G03", "pass" if canonical.has_regular_hours else "fail", evidence, {"days": str(days)})


def get_special_hours_check(canonical: CanonicalProfile) -> CheckResult:
    """Returns G04: special hours set; Google only shows them for the coming week, so their absence is `unknown`."""
    if canonical.special_days:
        return get_check_result("G04", "pass", Evidence(found=", ".join(canonical.special_days), url=canonical.google_maps_uri))
    return get_check_result(
        "G04",
        "unknown",
        Evidence(url=canonical.google_maps_uri),
        reason_ro="Google arată programul de sărbători doar pentru următoarele 7 zile, așa că nu îl putem verifica dinainte.",
    )


def get_photos_check(canonical: CanonicalProfile) -> CheckResult:
    """Returns G05: at least five photos (Places returns at most ten)."""
    count = canonical.photo_count
    status = "pass" if count >= MIN_PHOTOS else "partial" if count >= MIN_PHOTOS_PARTIAL else "fail"
    params = {"photos": get_count_phrase(count, "fotografie", "fotografii")}
    return get_check_result(
        "G05", status, Evidence(found=str(count), expected=str(MIN_PHOTOS), url=canonical.google_maps_uri), params
    )


def get_presence_check(check_id: str, value: str | None, url: str | None) -> CheckResult:
    """Returns a check that passes when the profile states a value (website, phone, price)."""
    return get_check_result(check_id, "pass" if value else "fail", Evidence(found=value, url=url))


def get_yes_no_check(check_id: str, answer: YesNoUnknown | None) -> CheckResult:
    """Returns a self-reported check: „da” passes, „nu” fails, „nu știu” or skipped is `unknown`."""
    if answer == "da":
        return get_check_result(check_id, "pass", Evidence(found=answer))
    if answer == "nu":
        return get_check_result(check_id, "fail", Evidence(found=answer))
    return get_check_result(check_id, "unknown", reason_ro=SELF_REPORT_UNKNOWN_RO)


def get_recent_post_check(answer: PostRecency | None) -> CheckResult:
    """Returns G09: a Google post in the last 30 days, as the owner reported it."""
    if answer == "luna_asta":
        return get_check_result("G09", "pass", Evidence(found=answer))
    if answer in ("mai_demult", "niciodata"):
        when = "Ai spus că ultima postare e de mai demult." if answer == "mai_demult" else "Ai spus că n-ai postat niciodată."
        return get_check_result("G09", "fail", Evidence(found=answer, expected="luna_asta"), {"when": when})
    return get_check_result("G09", "unknown", reason_ro=SELF_REPORT_UNKNOWN_RO)


def get_attributes_check(business_type: BusinessType, canonical: CanonicalProfile) -> CheckResult:
    """Returns G10: the share of the attributes that matter for the business type that are filled in (yes or no)."""
    expected = TYPE_ATTRIBUTES[business_type]
    missing = [attribute for attribute in expected if attribute not in canonical.attributes]
    share = (len(expected) - len(missing)) / len(expected)
    status = "pass" if not missing else "partial" if share >= 0.5 else "fail"
    params = {"missing": get_list_phrase([ATTRIBUTE_LABELS_RO[attribute] for attribute in missing])}
    evidence = Evidence(
        found=", ".join(sorted(canonical.attributes)), expected=", ".join(expected), url=canonical.google_maps_uri
    )
    return get_check_result("G10", status, evidence, params, earned_share=share)
