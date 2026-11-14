"""Loading a scan's data and marking its problems as fixed, shared by both devs' endpoints."""

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session

from app.config import BACKEND_DIR
from app.db import ScanRow, get_session
from app.errors import ApiError
from app.models import Chapter, ChapterId, Facts, Report, ScanInputs, ScoreUpdate
from app.pipeline.assemble import build_facts
from app.pipeline.problems import build_chapters
from app.pipeline.scoring import refresh_report_totals
from app.pipeline.types import ScanInternal

FIXTURES_DIR = BACKEND_DIR / "fixtures"
"""The directory holding the demo report and facts."""

edit_lock = threading.Lock()
"""Serializes report edits, so two quick „Am rezolvat” clicks can't overwrite each other."""


class ScanNotFound(ApiError):
    """Raised for a scan ID that doesn't exist, or a scan that failed without a report."""

    def __init__(self, scan_id: str) -> None:
        super().__init__("scan_not_found")
        self.scan_id = scan_id


class ScanRunning(ApiError):
    """Raised when a scan's report is needed while the scan is still running."""

    def __init__(self, scan_id: str) -> None:
        super().__init__("scan_running")
        self.scan_id = scan_id


class CheckNotFound(ApiError):
    """Raised for a check ID that isn't a problem of the scan, or, when unmarking, isn't marked as fixed."""

    def __init__(self, check_id: str) -> None:
        super().__init__("check_not_found")
        self.check_id = check_id


def get_scan_row(session: Session, scan_id: str) -> ScanRow:
    """Returns the scan row, or raises `ScanNotFound`."""
    row = session.get(ScanRow, scan_id)
    if row is None:
        raise ScanNotFound(scan_id)
    return row


def get_row_report(row: ScanRow) -> Report:
    """Returns the report stored on a scan row, or raises `ScanRunning` / `ScanNotFound` when there is none."""
    if row.report is not None:
        return Report.model_validate_json(row.report)
    if row.status == "running":
        raise ScanRunning(row.id)
    raise ScanNotFound(row.id)


def load_report(scan_id: str) -> Report:
    """Returns the current report of a scan."""
    with get_session() as session:
        return get_row_report(get_scan_row(session, scan_id))


def load_inputs(scan_id: str) -> ScanInputs:
    """Returns the onboarding inputs a scan was started with."""
    with get_session() as session:
        return ScanInputs.model_validate_json(get_scan_row(session, scan_id).inputs)


def load_facts(scan_id: str) -> Facts:
    """Returns the facts fix texts and the info page are written from, once the scan has a report."""
    with get_session() as session:
        row = get_scan_row(session, scan_id)
        get_row_report(row)
        inputs = ScanInputs.model_validate_json(row.inputs)
        internal = ScanInternal.model_validate_json(row.internal)
    if internal.source == "fixture":
        return Facts.model_validate_json((FIXTURES_DIR / "boema_facts.json").read_text(encoding="utf-8"))
    return build_facts(inputs, internal)


def get_chapter(report: Report, chapter_id: ChapterId) -> Chapter:
    """Returns the chapter with the given ID."""
    return next(chapter for chapter in report.chapters if chapter.id == chapter_id)


@contextmanager
def edit_report(scan_id: str) -> Iterator[tuple[Report, ScanInternal]]:
    """Yields a scan's report and internal data for editing, then refreshes the totals and saves both, one edit at a time."""
    with edit_lock, get_session() as session:
        row = get_scan_row(session, scan_id)
        report = get_row_report(row)
        internal = ScanInternal.model_validate_json(row.internal)
        yield report, internal
        refresh_report_totals(report)
        row.report = report.model_dump_json()
        row.internal = internal.model_dump_json()
        session.add(row)
        session.commit()


def mark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate:
    """Marks open problems as fixed by the owner, adds their points provisionally and returns the new scores.

    Check IDs already marked as fixed stay marked; the update reports the chapter of the first check ID.
    """
    return set_checks_claimed(scan_id, check_ids, claimed=True)


def unmark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate:
    """Reopens problems the owner had marked as fixed, removes their points and returns the new scores."""
    return set_checks_claimed(scan_id, check_ids, claimed=False)


def set_checks_claimed(scan_id: str, check_ids: list[str], claimed: bool) -> ScoreUpdate:
    """Sets or clears „fixed by the owner” on checks, rebuilds the chapters and returns the first check's score update."""
    if not check_ids:
        raise CheckNotFound("")
    with edit_report(scan_id) as (report, internal):
        overall_before = report.overall_exact
        checks = {check.check_id: check for check in internal.checks}
        for check_id in check_ids:
            check = checks.get(check_id)
            is_problem = check is not None and check.status in ("fail", "partial") and check.chapter_id != "cunoaste"
            if check is None or not is_problem or (not claimed and not check.claimed_fixed):
                raise CheckNotFound(check_id)
            check.claimed_fixed = claimed
        chapter_id = checks[check_ids[0]].chapter_id
        score_before = get_chapter(report, chapter_id).score or 0
        report.chapters = build_chapters(internal.checks, report.business)
    chapter_score = get_chapter(report, chapter_id).score or 0
    return ScoreUpdate(
        chapter_id=chapter_id,
        chapter_score=chapter_score,
        chapter_points_added=chapter_score - score_before,
        overall=report.overall,
        overall_exact=report.overall_exact,
        overall_delta=round(report.overall_exact - overall_before, 2),
        report=report,
    )
