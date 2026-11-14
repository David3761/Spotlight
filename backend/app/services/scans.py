"""Starting scans, reading their status and streaming their progress."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from app import jobs
from app.db import ScanRow, get_session
from app.models import CompleteEvent, FailedEvent, Report, ScanEnvelope, ScanEvent, ScanInputs, StepEvent
from app.pipeline.types import ScanInternal
from app.services.resolution import edit_report, get_row_report, get_scan_row, load_inputs

GEMINI_TEST_STUB_SECONDS = 2.0
"""How long the stubbed Gemini re-test waits before answering."""


def create_scan(inputs: ScanInputs) -> str:
    """Saves a new running scan, starts its analysis and returns its ID."""
    scan_id = uuid.uuid4().hex
    with get_session() as session:
        session.add(
            ScanRow(
                id=scan_id,
                created_at=datetime.now(UTC),
                status="running",
                inputs=inputs.model_dump_json(),
                internal=ScanInternal(source="fixture").model_dump_json(),
            )
        )
        session.commit()
    jobs.start_scan(scan_id)
    return scan_id


def rescan(scan_id: str) -> str:
    """Starts a new scan with the same inputs as an earlier one and returns its ID."""
    return create_scan(load_inputs(scan_id))


def get_envelope(scan_id: str) -> ScanEnvelope:
    """Returns a scan's status and, once complete, its report."""
    with get_session() as session:
        row = get_scan_row(session, scan_id)
        report = get_row_report(row) if row.status == "complete" else None
        return ScanEnvelope(scan_id=row.id, status=row.status, report=report, error_ro=row.error)


def get_events(scan_id: str) -> AsyncIterator[ScanEvent]:
    """Returns a scan's progress events, past ones first; raises `ScanNotFound` before any streaming starts."""
    with get_session() as session:
        row = get_scan_row(session, scan_id)
        report = get_row_report(row) if row.status == "complete" else None
        error = row.error
    progress = jobs.progress_by_scan.get(scan_id)
    if progress is not None:
        return progress.subscribe()
    return get_stored_events(scan_id, report, error)


async def get_stored_events(scan_id: str, report: Report | None, error: str | None) -> AsyncIterator[ScanEvent]:
    """Yields the outcome of a scan from before the server started: its `done` steps and `complete`, or `failed`."""
    if report is None:
        yield FailedEvent(type="failed", message_ro=error or jobs.INTERRUPTED_ERROR_RO)
        return
    for step, detail_ro in jobs.get_step_details(report):
        yield StepEvent(type="step", step=step, status="done", detail_ro=detail_ro)
    yield CompleteEvent(type="complete", scan_id=scan_id)


async def run_gemini_test(scan_id: str) -> Report:
    """Reruns the live Gemini test and returns the updated report."""
    with get_session() as session:
        get_row_report(get_scan_row(session, scan_id))
    await asyncio.sleep(GEMINI_TEST_STUB_SECONDS)
    with edit_report(scan_id) as (report, _):
        report.gemini.last_checked = datetime.now(UTC).isoformat()
    return report
