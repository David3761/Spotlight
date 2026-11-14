"""Loading a scan's data and marking its problems as fixed, shared by both devs' endpoints."""

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session

from app.config import BACKEND_DIR
from app.db import ScanRow, get_session
from app.errors import ApiError
from app.models import Chapter, ChapterId, Facts, Problem, Report, ScanInputs, ScoreUpdate, SolvedItem
from app.pipeline.problems import build_chapters
from app.pipeline.scoring import refresh_report_totals
from app.pipeline.types import ClaimedProblem, ScanInternal

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
    """Raised for a check ID that is not an open problem (or, when unmarking, not a problem marked as fixed)."""

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
    """Returns the facts fix texts and the info page are written from."""
    with get_session() as session:
        get_scan_row(session, scan_id)
    return Facts.model_validate_json((FIXTURES_DIR / "boema_facts.json").read_text(encoding="utf-8"))


def get_chapter(report: Report, chapter_id: ChapterId) -> Chapter:
    """Returns the chapter with the given ID."""
    return next(chapter for chapter in report.chapters if chapter.id == chapter_id)


def get_open_problem(report: Report, check_id: str) -> Problem:
    """Returns the open problem with the given check ID, or raises `CheckNotFound`."""
    for chapter in report.chapters:
        for problem in chapter.problems:
            if problem.check_id == check_id:
                return problem
    raise CheckNotFound(check_id)


def get_claimed_chapter(internal: ScanInternal, check_id: str) -> ChapterId:
    """Returns the chapter of a problem marked as fixed, or raises `CheckNotFound`."""
    claimed = internal.claimed_problems.get(check_id)
    if claimed is None:
        raise CheckNotFound(check_id)
    return claimed.problem.chapter_id


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


def get_score_update(report: Report, chapter_id: ChapterId, points_added: int, overall_before: float) -> ScoreUpdate:
    """Returns the score update for a changed chapter."""
    return ScoreUpdate(
        chapter_id=chapter_id,
        chapter_score=get_chapter(report, chapter_id).score or 0,
        chapter_points_added=points_added,
        overall=report.overall,
        overall_exact=report.overall_exact,
        overall_delta=round(report.overall_exact - overall_before, 2),
        report=report,
    )


def mark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate:
    """Marks open problems as fixed by the owner, adds their points provisionally and returns the new scores.

    Check IDs already marked as fixed are skipped; the update reports the chapter of the first check ID.
    """
    if not check_ids:
        raise CheckNotFound("")
    with edit_report(scan_id) as (report, internal):
        overall_before = report.overall_exact
        if internal.source == "pipeline":
            chapter_id, points_added = set_checks_claimed(report, internal, check_ids, claimed=True)
        else:
            chapter_id, points_added = claim_fixture_problems(report, internal, check_ids)
    return get_score_update(report, chapter_id, points_added, overall_before)


def unmark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate:
    """Reopens problems the owner had marked as fixed, removes the points they added and returns the new scores."""
    if not check_ids:
        raise CheckNotFound("")
    with edit_report(scan_id) as (report, internal):
        overall_before = report.overall_exact
        if internal.source == "pipeline":
            chapter_id, points_added = set_checks_claimed(report, internal, check_ids, claimed=False)
        else:
            chapter_id, points_added = reopen_fixture_problems(report, internal, check_ids)
    return get_score_update(report, chapter_id, points_added, overall_before)


def set_checks_claimed(report: Report, internal: ScanInternal, check_ids: list[str], claimed: bool) -> tuple[ChapterId, int]:
    """Sets or clears „fixed by the owner” on checks and rebuilds the chapters; returns the first chapter and its score change."""
    checks = {check.check_id: check for check in internal.checks}
    for check_id in check_ids:
        check = checks.get(check_id)
        is_open_problem = check is not None and check.status in ("fail", "partial") and check.chapter_id != "cunoaste"
        if check is None or not is_open_problem or (not claimed and not check.claimed_fixed):
            raise CheckNotFound(check_id)
        check.claimed_fixed = claimed
    chapter_id = checks[check_ids[0]].chapter_id
    score_before = get_chapter(report, chapter_id).score or 0
    report.chapters = build_chapters(internal.checks, report.business)
    return chapter_id, (get_chapter(report, chapter_id).score or 0) - score_before


def claim_fixture_problems(report: Report, internal: ScanInternal, check_ids: list[str]) -> tuple[ChapterId, int]:
    """Moves open problems of a fixture report to solved and adds their points; returns the first chapter and its score change."""
    chapter_id: ChapterId | None = None
    points_added = 0
    for check_id in check_ids:
        if check_id in internal.claimed_problems:
            continue
        problem = get_open_problem(report, check_id)
        chapter = get_chapter(report, problem.chapter_id)
        score_before = chapter.score or 0
        chapter.problems.remove(problem)
        chapter.score = min(100, score_before + problem.points)
        chapter.solved.append(
            SolvedItem(check_id=check_id, title_ro=problem.title_ro, source="claimed_fixed", points=problem.points)
        )
        internal.claimed_problems[check_id] = ClaimedProblem(problem=problem, score_added=chapter.score - score_before)
        chapter_id = chapter_id or problem.chapter_id
        if problem.chapter_id == chapter_id:
            points_added += chapter.score - score_before
    return chapter_id or get_claimed_chapter(internal, check_ids[0]), points_added


def reopen_fixture_problems(report: Report, internal: ScanInternal, check_ids: list[str]) -> tuple[ChapterId, int]:
    """Reopens problems of a fixture report and removes their points; returns the first chapter and its score change."""
    chapter_id = get_claimed_chapter(internal, check_ids[0])
    points_removed = 0
    for check_id in check_ids:
        claimed = internal.claimed_problems.pop(check_id, None)
        if claimed is None:
            raise CheckNotFound(check_id)
        chapter = get_chapter(report, claimed.problem.chapter_id)
        chapter.solved = [item for item in chapter.solved if item.check_id != check_id]
        chapter.problems.append(claimed.problem)
        chapter.score = (chapter.score or 0) - claimed.score_added
        if claimed.problem.chapter_id == chapter_id:
            points_removed += claimed.score_added
    return chapter_id, -points_removed
