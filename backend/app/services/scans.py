"""Starting scans, reading their status and streaming their progress."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from app import jobs
from app.db import ScanRow, get_session
from app.errors import ApiError
from app.models import (
    CompleteEvent,
    FailedEvent,
    Report,
    ScanEnvelope,
    ScanEvent,
    ScanInputs,
    StepEvent,
)
from app.pipeline.collectors.live_test import collect_live_test
from app.pipeline.collectors.rivals import get_comparison, get_rival_rows
from app.pipeline.types import ScanInternal
from app.services.resolution import (
    edit_report,
    get_row_report,
    get_scan_row,
    load_inputs,
)

DEMO_GEMINI_TEST_SECONDS = 2.0
"""How long „Testează din nou” pauses on a demo scan, so the button's busy state shows."""


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
                internal=ScanInternal(source="fixture" if jobs.is_demo_scan(inputs) else "pipeline").model_dump_json(),
            )
        )
        session.commit()
    jobs.start_scan(scan_id, inputs)
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
    """Reruns only the live Gemini test, numbered by the current time so no answer comes from the cache, and returns the report.

    A demo scan keeps the demo's Gemini block and only refreshes its time, after a short pause.
    """
    with get_session() as session:
        row = get_scan_row(session, scan_id)
        get_row_report(row)
        inputs = ScanInputs.model_validate_json(row.inputs)
        internal = ScanInternal.model_validate_json(row.internal)
    if internal.source == "fixture":
        await asyncio.sleep(DEMO_GEMINI_TEST_SECONDS)
        with edit_report(scan_id) as (report, _):
            report.gemini.last_checked = datetime.now(UTC).isoformat()
        return report
    round_number = int(datetime.now(UTC).timestamp())
    live = await jobs.run_collector(
        collect_live_test(inputs, internal.canonical, round_number), jobs.LIVE_TEST_TIMEOUT_SECONDS, None
    )
    if live is None:
        raise ApiError("upstream_error", "Nu am putut întreba Gemini acum. Încearcă din nou peste un minut.")
    rival_rows = await jobs.run_collector(get_rival_rows(live.rivals), jobs.RIVALS_TIMEOUT_SECONDS, [])
    with edit_report(scan_id) as (report, internal):
        report.gemini = live.block
        report.comparison = get_comparison(report.comparison.me, rival_rows, internal.checks)
    return report
