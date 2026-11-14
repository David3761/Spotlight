"""Background scan jobs and the in-memory progress bus the SSE stream reads from."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from urllib.parse import urlparse

from pydantic import TypeAdapter
from sqlmodel import select

from app.db import ScanRow, get_session
from app.models import CompleteEvent, FailedEvent, Report, ScanEvent, StepEvent, StepId
from app.pipeline.romanian import get_count_phrase
from app.pipeline.types import CheckResult, ScanInternal
from app.services.resolution import FIXTURES_DIR

FIXTURE_STEP_SECONDS = 0.8
"""The pause between fixture replay events, so the five steps take about 8 seconds."""

CHECK_LIST = TypeAdapter(list[CheckResult])
"""Parses a JSON list of check results."""

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


def start_scan(scan_id: str) -> None:
    """Creates the progress bus for a scan and starts its analysis in the background."""
    progress = ScanProgress()
    progress_by_scan[scan_id] = progress
    task = asyncio.create_task(replay_fixture(scan_id, progress))
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
    review_count = report.comparison.me.review_count or 0
    website = report.business.website
    return [
        ("google", "Am găsit Profilul tău Google"),
        ("recenzii", f"Am găsit {get_count_phrase(review_count, 'recenzie', 'recenzii')}"),
        ("website", f"Am citit {urlparse(website).netloc.removeprefix('www.')}" if website else "Am verificat site-ul"),
        ("retele", "Am verificat Instagram"),
        ("gemini", f"I-am pus lui Gemini {get_count_phrase(report.gemini.total, 'întrebare', 'întrebări')}"),
    ]


async def replay_fixture(scan_id: str, progress: ScanProgress) -> None:
    """Plays the five progress steps over about 8 seconds, then saves the demo report and completes the scan."""
    try:
        report = get_fixture_report(scan_id)
        for step, detail_ro in get_step_details(report):
            await progress.publish(StepEvent(type="step", step=step, status="running", detail_ro=None))
            await asyncio.sleep(FIXTURE_STEP_SECONDS)
            await progress.publish(StepEvent(type="step", step=step, status="done", detail_ro=detail_ro))
            await asyncio.sleep(FIXTURE_STEP_SECONDS)
        save_report(scan_id, report, get_fixture_checks())
        await progress.publish(CompleteEvent(type="complete", scan_id=scan_id))
    except Exception:
        save_failure(scan_id, "Nu am putut termina analiza.")
        await progress.publish(FailedEvent(type="failed", message_ro="Nu am putut termina analiza."))
        raise


def save_report(scan_id: str, report: Report, checks: list[CheckResult]) -> None:
    """Stores the finished report with the checks it was scored from and marks the scan complete."""
    with get_session() as session:
        row = session.get(ScanRow, scan_id)
        if row is None:
            return
        internal = ScanInternal.model_validate_json(row.internal)
        internal.checks = checks
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
