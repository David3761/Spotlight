"""Background scan jobs and the in-memory progress bus the SSE stream reads from."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import TypeAdapter
from sqlmodel import select

from app.config import get_settings
from app.db import ScanRow, get_session
from app.models import (
    ChapterId,
    CompareRow,
    Comparison,
    CompleteEvent,
    FailedEvent,
    Report,
    ScanEvent,
    ScanInputs,
    StepEvent,
    StepId,
)
from app.pipeline.assemble import (
    build_report,
    get_compare_row,
    get_unknown_gemini_block,
)
from app.pipeline.canonical import CanonicalProfile, get_canonical
from app.pipeline.collectors.competitors import NearbyCompetitor, get_nearby_competitors
from app.pipeline.collectors.google_profile import collect_google_profile
from app.pipeline.collectors.listings import LISTING_CHECK_IDS, collect_listings
from app.pipeline.collectors.mentions import MENTION_CHECK_IDS, collect_mentions
from app.pipeline.collectors.reviews import collect_reviews
from app.pipeline.collectors.social import SOCIAL_CHECK_IDS, collect_social
from app.pipeline.collectors.training_probe import PROBE_CHECK_IDS, PROBE_QUESTION_COUNT, collect_training_probe
from app.pipeline.collectors.website import (
    CONTENT_CHECK_IDS,
    TECH_CHECK_IDS,
    WebsiteScan,
    collect_website,
    get_website_url,
)
from app.pipeline.resolve import search_places
from app.pipeline.romanian import get_count_phrase
from app.pipeline.scoring import get_unknown_results
from app.pipeline.types import CheckResult, ScanInternal
from app.services.resolution import FIXTURES_DIR

logger = logging.getLogger(__name__)

FIXTURE_STEP_SECONDS = 0.8
"""The pause between fixture replay events, so the five steps take about 8 seconds."""

CHECK_LIST = TypeAdapter(list[CheckResult])
"""Parses a JSON list of check results."""

GOOGLE_TIMEOUT_SECONDS = 15
"""The time limit of the Google profile collector (3.1)."""

GOOGLE_CHECK_IDS = [f"G{number:02d}" for number in range(2, 13)]
"""The checks the Google profile collector reports when it runs."""

NEARBY_TIMEOUT_SECONDS = 15
"""The time limit of the nearby competitors search (3.9a)."""

REVIEWS_TIMEOUT_SECONDS = 30
"""The time limit of the reviews collector (3.2)."""

REVIEW_CHECK_IDS = ["R01", "R02", "R03", "R04", "R05"]
"""The checks the reviews collector reports."""

WEBSITE_TIMEOUT_SECONDS = 45
"""The time limit of the website collector (3.3), PageSpeed's 40 s included."""

PRESENCE_COLLECTOR_TIMEOUT_SECONDS = 30
"""The time limit of each of the listings, mentions and social collectors (3.4–3.6)."""

PRESENCE_TIMEOUT_SECONDS = 80
"""The time limit of the `retele` step: the website collector it waits for, then its own collectors."""

PROBE_TIMEOUT_SECONDS = 30
"""The time limit of the training-data probe (3.7)."""

COLLECTOR_ERROR_RO = "Nu am putut verifica acum. Încearcă din nou mai târziu."
"""Why a check couldn't run when its collector failed or took too long."""

PROFILE_ERROR_RO = "Nu am putut citi Profilul tău Google. Încearcă din nou."
"""Why a scan failed when the Google profile couldn't be fetched."""

PIPELINE_ERROR_RO = "Nu am putut termina analiza."
"""Why a scan failed after the profile was fetched."""

INTERRUPTED_ERROR_RO = "Analiza s-a oprit înainte să se termine. Pornește una nouă."
"""The error shown for a scan that was still running when the server stopped."""


class ScanProgress:
    """The events of one scan so far; every subscriber gets all of them, from the first."""

    def __init__(self) -> None:
        self.events: list[ScanEvent] = []
        self.changed = asyncio.Condition()

    async def publish(self, event: ScanEvent) -> None:
        """Appends an event and wakes the subscribers."""
        async with self.changed:
            self.events.append(event)
            self.changed.notify_all()

    async def subscribe(self) -> AsyncIterator[ScanEvent]:
        """Yields every event from the first, waiting for new ones until `complete` or `failed`."""
        index = 0
        while True:
            async with self.changed:
                await self.changed.wait_for(lambda seen=index: len(self.events) > seen)
                new_events = self.events[index:]
            index += len(new_events)
            for event in new_events:
                yield event
                if not isinstance(event, StepEvent):
                    return


progress_by_scan: dict[str, ScanProgress] = {}
"""The progress of every scan started since the server started."""

running_tasks: set[asyncio.Task[None]] = set()
"""Strong references to running scan tasks, so they aren't garbage-collected."""


def fail_interrupted_scans() -> None:
    """Marks scans a previous server process left running as failed, since their progress was lost with it."""
    with get_session() as session:
        for row in session.exec(select(ScanRow).where(ScanRow.status == "running")).all():
            row.status = "failed"
            row.error = INTERRUPTED_ERROR_RO
            session.add(row)
        session.commit()


def is_demo_scan(inputs: ScanInputs) -> bool:
    """Returns whether a scan replays the demo report: demo mode is on and the owner picked the demo place."""
    settings = get_settings()
    return settings.demo_mode == "fixture" and bool(settings.demo_place_id) and inputs.place_id == settings.demo_place_id


def start_scan(scan_id: str, inputs: ScanInputs) -> None:
    """Creates the progress bus for a scan and starts its analysis, or the demo replay, in the background."""
    progress = ScanProgress()
    progress_by_scan[scan_id] = progress
    job = replay_fixture(scan_id, progress) if is_demo_scan(inputs) else run_pipeline(scan_id, inputs, progress)
    task = asyncio.create_task(job)
    running_tasks.add(task)
    task.add_done_callback(running_tasks.discard)


def get_fixture_report(scan_id: str) -> Report:
    """Returns the demo report with a new scan ID and the current time."""
    report = Report.model_validate_json((FIXTURES_DIR / "boema_report.json").read_text(encoding="utf-8"))
    report.scan_id = scan_id
    report.checked_at = datetime.now(UTC).isoformat()
    report.gemini.last_checked = report.checked_at
    return report


def get_fixture_checks() -> list[CheckResult]:
    """Returns the check results the demo report was scored from."""
    return CHECK_LIST.validate_json((FIXTURES_DIR / "boema_checks.json").read_text(encoding="utf-8"))


def get_step_details(report: Report) -> list[tuple[StepId, str]]:
    """Returns the progress steps with the done text each would show for this report."""
    return [
        ("google", get_google_detail(report.business.place_id is not None)),
        ("recenzii", get_reviews_detail(report.comparison.me.review_count)),
        ("website", get_website_detail(report.business.website, get_chapter_score(report, "continut") is not None)),
        ("retele", get_social_detail(get_chapter_score(report, "social") is not None)),
        ("gemini", get_gemini_detail(report.gemini.total)),
    ]


def get_chapter_score(report: Report, chapter_id: ChapterId) -> int | None:
    """Returns a chapter's score in a report."""
    return next(chapter.score for chapter in report.chapters if chapter.id == chapter_id)


def get_google_detail(has_profile: bool) -> str:
    """Returns the Google step's done text."""
    return "Am găsit Profilul tău Google" if has_profile else "Nu am găsit un Profil Google"


def get_reviews_detail(review_count: int | None) -> str:
    """Returns the reviews step's done text: how many Google reviews there are."""
    return f"Am găsit {get_count_phrase(review_count, 'recenzie', 'recenzii')}" if review_count else "Nu am găsit recenzii"


def get_website_detail(website: str | None, was_read: bool) -> str:
    """Returns the website step's done text: the domain read, or why it wasn't."""
    if not website:
        return "Nu ai încă un site"
    domain = urlparse(website).netloc.removeprefix("www.")
    return f"Am citit {domain}" if was_read else f"Nu am putut citi {domain}"


def get_social_detail(was_checked: bool) -> str:
    """Returns the social step's done text."""
    return "Am verificat Instagram" if was_checked else "Nu am putut verifica Instagram"


def get_gemini_detail(questions: int) -> str:
    """Returns the Gemini step's done text: how many questions Gemini answered."""
    if not questions:
        return "Nu am putut întreba Gemini acum"
    return f"I-am pus lui Gemini {get_count_phrase(questions, 'întrebare', 'întrebări')}"


async def replay_fixture(scan_id: str, progress: ScanProgress) -> None:
    """Plays the five progress steps over about 8 seconds, then saves the demo report and completes the scan."""
    try:
        report = get_fixture_report(scan_id)
        for step, detail_ro in get_step_details(report):
            await progress.publish(StepEvent(type="step", step=step, status="running", detail_ro=None))
            await asyncio.sleep(FIXTURE_STEP_SECONDS)
            await progress.publish(StepEvent(type="step", step=step, status="done", detail_ro=detail_ro))
            await asyncio.sleep(FIXTURE_STEP_SECONDS)
        save_report(scan_id, report, ScanInternal(source="fixture", checks=get_fixture_checks()))
        await progress.publish(CompleteEvent(type="complete", scan_id=scan_id))
    except Exception:
        save_failure(scan_id, PIPELINE_ERROR_RO)
        await progress.publish(FailedEvent(type="failed", message_ro=PIPELINE_ERROR_RO))
        raise


async def run_pipeline(scan_id: str, inputs: ScanInputs, progress: ScanProgress) -> None:
    """Runs the analysis (§5): finds the profile, runs the collectors, scores, saves the report and completes the scan.

    The scan fails only when the Google profile can't be fetched; a failed or slow collector leaves its checks `unknown`.
    """
    await progress.publish(StepEvent(type="step", step="google", status="running", detail_ro=None))
    try:
        canonical = await get_scan_canonical(inputs)
    except Exception:
        logger.exception("Steps 1-2 failed for scan %s", scan_id)
        save_failure(scan_id, PROFILE_ERROR_RO)
        await progress.publish(FailedEvent(type="failed", message_ro=PROFILE_ERROR_RO))
        return
    try:
        nearby = await get_nearby(inputs, canonical)
        google_checks = await run_collector(
            collect_google_profile(inputs, canonical),
            GOOGLE_TIMEOUT_SECONDS,
            get_unknown_results(GOOGLE_CHECK_IDS, COLLECTOR_ERROR_RO),
        )
        await progress.publish(
            StepEvent(type="step", step="google", status="done", detail_ro=get_google_detail(canonical is not None))
        )
        review_count = canonical.review_count if canonical else None
        website = get_website_url(inputs, canonical)
        website_step = asyncio.create_task(
            run_step(
                progress,
                "website",
                collect_website(inputs, canonical),
                WEBSITE_TIMEOUT_SECONDS,
                WebsiteScan(
                    checks=get_unknown_results(CONTENT_CHECK_IDS + TECH_CHECK_IDS, COLLECTOR_ERROR_RO), facts=None, links=[]
                ),
                lambda scan: get_website_detail(website, has_known(scan.checks, "C")),
            )
        )
        review_checks, website_scan, presence_checks, probe_checks = await asyncio.gather(
            run_step(
                progress,
                "recenzii",
                collect_reviews(inputs, canonical, nearby),
                REVIEWS_TIMEOUT_SECONDS,
                get_unknown_results(REVIEW_CHECK_IDS, COLLECTOR_ERROR_RO),
                lambda _: get_reviews_detail(review_count),
            ),
            website_step,
            run_step(
                progress,
                "retele",
                collect_presence(inputs, canonical, website_step),
                PRESENCE_TIMEOUT_SECONDS,
                get_unknown_results(LISTING_CHECK_IDS + MENTION_CHECK_IDS + SOCIAL_CHECK_IDS, COLLECTOR_ERROR_RO),
                lambda checks: get_social_detail(has_known(checks, "S")),
            ),
            run_step(
                progress,
                "gemini",
                collect_training_probe(inputs, canonical),
                PROBE_TIMEOUT_SECONDS,
                get_unknown_results(PROBE_CHECK_IDS, COLLECTOR_ERROR_RO),
                lambda checks: get_gemini_detail(PROBE_QUESTION_COUNT if has_known(checks) else 0),
            ),
        )
        all_checks = google_checks + review_checks + website_scan.checks + presence_checks + probe_checks
        me = (
            get_compare_row(canonical)
            if canonical
            else CompareRow(
                name=inputs.business_name,
                place_id=None,
                review_count=None,
                rating=None,
                photo_count=None,
                photo_count_capped=False,
                hours_complete=None,
            )
        )
        comparison = Comparison(me=me, rivals=[], insights_ro=[], actions=[])
        report = build_report(scan_id, inputs, canonical, all_checks, get_unknown_gemini_block(), comparison)
        internal = ScanInternal(
            source="pipeline",
            checks=all_checks,
            canonical=canonical,
            website_facts=website_scan.facts,
            site_links=website_scan.links,
        )
        save_report(scan_id, report, internal)
        await progress.publish(CompleteEvent(type="complete", scan_id=scan_id))
    except Exception:
        logger.exception("Pipeline failed for scan %s", scan_id)
        save_failure(scan_id, PIPELINE_ERROR_RO)
        await progress.publish(FailedEvent(type="failed", message_ro=PIPELINE_ERROR_RO))


async def get_scan_canonical(inputs: ScanInputs) -> CanonicalProfile | None:
    """Returns the business's Google profile (steps 1–2), or `None` when the owner has none or search finds no match."""
    if inputs.no_google_profile:
        return None
    place_id = inputs.place_id
    if place_id is None:
        candidates = await search_places(inputs.business_name, inputs.city, inputs.neighborhood)
        place_id = candidates[0].place_id if candidates and candidates[0].best else None
    return await get_canonical(place_id) if place_id else None


async def get_nearby(inputs: ScanInputs, canonical: CanonicalProfile | None) -> list[NearbyCompetitor]:
    """Returns the nearby competitors (3.9a), or none when there's no profile or the search fails."""
    if canonical is None:
        return []
    try:
        return await asyncio.wait_for(get_nearby_competitors(inputs.business_type, canonical), NEARBY_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Nearby search failed")
        return []


async def run_step[T](
    progress: ScanProgress,
    step: StepId,
    collector: Coroutine[Any, Any, T],
    timeout: float,
    fallback: T,
    get_detail: Callable[[T], str],
) -> T:
    """Runs one progress step's collector, announcing it as running and then done with its detail text."""
    await progress.publish(StepEvent(type="step", step=step, status="running", detail_ro=None))
    result = await run_collector(collector, timeout, fallback)
    await progress.publish(StepEvent(type="step", step=step, status="done", detail_ro=get_detail(result)))
    return result


async def collect_presence(
    inputs: ScanInputs, canonical: CanonicalProfile | None, website_step: asyncio.Task[WebsiteScan]
) -> list[CheckResult]:
    """Runs listings, mentions and social (3.4–3.6), each with its own time limit; a failed one leaves its checks `unknown`.

    Mentions starts at once; listings and social wait for the website's links. The shield keeps this step's
    time limit from cancelling the website step it waits on.
    """
    mentions = asyncio.create_task(
        run_collector(
            collect_mentions(inputs, canonical),
            PRESENCE_COLLECTOR_TIMEOUT_SECONDS,
            get_unknown_results(MENTION_CHECK_IDS, COLLECTOR_ERROR_RO),
        )
    )
    try:
        website = await asyncio.shield(website_step)
        listing_checks, social_checks = await asyncio.gather(
            run_collector(
                collect_listings(inputs, canonical, website.links),
                PRESENCE_COLLECTOR_TIMEOUT_SECONDS,
                get_unknown_results(LISTING_CHECK_IDS, COLLECTOR_ERROR_RO),
            ),
            run_collector(
                collect_social(inputs, canonical, website.links),
                PRESENCE_COLLECTOR_TIMEOUT_SECONDS,
                get_unknown_results(SOCIAL_CHECK_IDS, COLLECTOR_ERROR_RO),
            ),
        )
        return listing_checks + await mentions + social_checks
    finally:
        mentions.cancel()


def has_known(checks: list[CheckResult], prefixes: str = "") -> bool:
    """Returns whether any of the checks (optionally only those with the given ID prefixes) could run."""
    return any(check.status != "unknown" for check in checks if not prefixes or check.check_id[0] in prefixes)


async def run_collector[T](collector: Coroutine[Any, Any, T], timeout: float, fallback: T) -> T:
    """Returns a collector's result, or the fallback (its checks as `unknown`) when it fails or runs past its timeout."""
    try:
        return await asyncio.wait_for(collector, timeout)
    except Exception:
        logger.exception("Collector failed or timed out")
        return fallback


def save_report(scan_id: str, report: Report, internal: ScanInternal) -> None:
    """Stores the finished report with the internal data it was built from and marks the scan complete."""
    with get_session() as session:
        row = session.get(ScanRow, scan_id)
        if row is None:
            return
        row.internal = internal.model_dump_json()
        row.report = report.model_dump_json()
        row.status = "complete"
        session.add(row)
        session.commit()


def save_failure(scan_id: str, error_ro: str) -> None:
    """Marks the scan failed with a Romanian error message."""
    with get_session() as session:
        row = session.get(ScanRow, scan_id)
        if row is None:
            return
        row.status = "failed"
        row.error = error_ro
        session.add(row)
        session.commit()
