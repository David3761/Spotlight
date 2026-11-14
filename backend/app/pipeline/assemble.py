"""Step 7: the report, the business card and the facts, assembled from the inputs, the Google profile and the checks."""

from datetime import UTC, datetime

from app.models import Business, CompareRow, Comparison, Facts, GeminiBlock, Platform, Report, ScanInputs
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.normalize import format_national_phone, get_instagram_handle
from app.pipeline.problems import build_chapters
from app.pipeline.scoring import GEMINI_WEIGHT, refresh_report_totals
from app.pipeline.types import CheckResult, ScanInternal

PLATFORM_LABELS: dict[Platform, str] = {
    "tripadvisor": "TripAdvisor",
    "glovo": "Glovo",
    "wolt": "Wolt",
    "bolt_food": "Bolt Food",
    "booking": "Booking",
    "booksy": "Booksy",
}
"""The display name of each platform."""

SUMMARIES_RO = [
    (70, "Gemini te poate recomanda. Mai sunt câteva detalii de pus la punct."),
    (40, "Ești pe drumul bun. Câteva lucruri simple te pot aduce mai sus."),
    (0, "Gemini te recomandă rar deocamdată. Multe se rezolvă în câteva minute."),
]
"""The line under the score ring, by the lowest overall score it applies to."""


def get_initials(name: str) -> str:
    """Returns the initials of the first two words of a name, e.g. „CB” for „Cafeneaua Boema”."""
    return "".join(word[0] for word in name.split()[:2]).upper()


def build_business(inputs: ScanInputs, canonical: CanonicalProfile | None) -> Business:
    """Returns the business card: Google's data where there is a profile, the owner's answers otherwise."""
    name = canonical.name if canonical else inputs.business_name
    return Business(
        name=name,
        initials=get_initials(name),
        type=inputs.business_type,
        type_label_ro=inputs.business_type_label_ro,
        city=inputs.city,
        neighborhood=inputs.neighborhood,
        place_id=canonical.place_id if canonical else None,
        address=canonical.formatted_address if canonical else None,
        phone=canonical.national_phone if canonical else None,
        website=(canonical.website if canonical else None) or inputs.website_url,
        google_maps_uri=canonical.google_maps_uri if canonical else None,
        instagram_url=inputs.instagram_url,
        instagram_handle=get_instagram_handle(inputs.instagram_url),
        tiktok_url=inputs.tiktok_url,
    )


def get_compare_row(canonical: CanonicalProfile) -> CompareRow:
    """Returns a business's row in the comparison table."""
    return CompareRow(
        name=canonical.name,
        place_id=canonical.place_id,
        review_count=canonical.review_count,
        rating=canonical.rating,
        photo_count=canonical.photo_count,
        photo_count_capped=canonical.photo_count >= 10,
        hours_complete=canonical.hours_complete,
    )


def get_unknown_gemini_block() -> GeminiBlock:
    """Returns the Gemini block of a scan whose live test didn't run."""
    return GeminiBlock(
        status="unknown",
        score=None,
        weight=GEMINI_WEIGHT,
        mentioned=0,
        total=0,
        last_checked=datetime.now(UTC).isoformat(),
        top_competitors=[],
        groups=[],
    )


def build_report(
    scan_id: str,
    inputs: ScanInputs,
    canonical: CanonicalProfile | None,
    checks: list[CheckResult],
    gemini: GeminiBlock,
    comparison: Comparison,
) -> Report:
    """Returns the full report: chapters from the checks, then every total derived from them."""
    business = build_business(inputs, canonical)
    report = Report(
        scan_id=scan_id,
        checked_at=datetime.now(UTC).isoformat(),
        business=business,
        overall=0,
        overall_exact=0.0,
        summary_ro="",
        open_problem_count=0,
        next_steps=[],
        gemini=gemini,
        chapters=build_chapters(checks, business),
        comparison=comparison,
    )
    refresh_report_totals(report)
    report.summary_ro = next(text for minimum, text in SUMMARIES_RO if report.overall >= minimum)
    return report


def build_facts(inputs: ScanInputs, internal: ScanInternal) -> Facts:
    """Returns the facts fix texts and the info page are written from: Google's profile, the owner's answers, the website."""
    canonical = internal.canonical
    phone = (canonical.phone_e164 or canonical.national_phone) if canonical else None
    return Facts(
        name=canonical.name if canonical else inputs.business_name,
        type_label_ro=inputs.business_type_label_ro,
        city=inputs.city,
        neighborhood=inputs.neighborhood,
        address=canonical.formatted_address if canonical else None,
        phone=format_national_phone(phone) if phone else None,
        website=(canonical.website if canonical else None) or inputs.website_url,
        google_maps_uri=canonical.google_maps_uri if canonical else None,
        hours_ro=canonical.hours_ro if canonical else [],
        special_hours_ro=canonical.special_days_ro if canonical else [],
        attributes_ro=canonical.attributes_ro if canonical else [],
        instagram_handle=get_instagram_handle(inputs.instagram_url),
        tiktok_url=inputs.tiktok_url,
        platforms_ro=[PLATFORM_LABELS[platform] for platform in inputs.platforms or []],
        website_facts=internal.website_facts,
    )
