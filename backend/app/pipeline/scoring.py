"""Scores: the check catalog, chapter weights and gates, the overall score and the totals derived from open problems."""

from typing import NamedTuple

from app.models import Chapter, ChapterId, CheckStatus, FixType, Problem, Report
from app.pipeline.types import CheckResult, Evidence

CHAPTER_WEIGHTS: dict[ChapterId, float] = {
    "profil": 0.20,
    "recenzii": 0.15,
    "continut": 0.15,
    "site": 0.10,
    "info": 0.10,
    "mentiuni": 0.10,
    "social": 0.05,
    "cunoaste": 0.05,
}
"""The weight of each chapter in the overall score, in chapter order."""

GEMINI_WEIGHT = 0.10
"""The weight of the live Gemini test in the overall score."""

NEXT_STEPS_COUNT = 3
"""How many open problems the dashboard lists as next steps."""

CONTINUT_GATE_CAP = 30
"""The highest content score when Gemini can't read the site (T01 fails, Googlebot blocked, or an empty shell)."""


class CatalogEntry(NamedTuple):
    """A check's chapter, points and who fixes it."""

    chapter_id: ChapterId
    points: int
    fix_type: FixType


CATALOG: dict[str, CatalogEntry] = {
    "G01": CatalogEntry("profil", 100, "owner_action"),
    "G02": CatalogEntry("profil", 10, "owner_action"),
    "G03": CatalogEntry("profil", 15, "owner_action"),
    "G04": CatalogEntry("profil", 10, "owner_action"),
    "G05": CatalogEntry("profil", 10, "owner_action"),
    "G06": CatalogEntry("profil", 10, "owner_action"),
    "G07": CatalogEntry("profil", 10, "owner_action"),
    "G08": CatalogEntry("profil", 10, "generate"),
    "G09": CatalogEntry("profil", 5, "generate"),
    "G10": CatalogEntry("profil", 5, "owner_action"),
    "G11": CatalogEntry("profil", 5, "owner_action"),
    "G12": CatalogEntry("profil", 10, "owner_action"),
    "R01": CatalogEntry("recenzii", 30, "owner_action"),
    "R02": CatalogEntry("recenzii", 20, "owner_action"),
    "R03": CatalogEntry("recenzii", 25, "owner_action"),
    "R04": CatalogEntry("recenzii", 15, "generate"),
    "R05": CatalogEntry("recenzii", 10, "owner_action"),
    "C01": CatalogEntry("continut", 15, "generate"),
    "C02": CatalogEntry("continut", 15, "generate"),
    "C03": CatalogEntry("continut", 15, "generate"),
    "C04": CatalogEntry("continut", 10, "generate"),
    "C05": CatalogEntry("continut", 15, "generate"),
    "C06": CatalogEntry("continut", 10, "dev_export"),
    "C07": CatalogEntry("continut", 10, "generate"),
    "C08": CatalogEntry("continut", 10, "generate"),
    "T01": CatalogEntry("site", 15, "dev_export"),
    "T02": CatalogEntry("site", 20, "dev_export"),
    "T03": CatalogEntry("site", 10, "dev_export"),
    "T04": CatalogEntry("site", 20, "dev_export"),
    "T05": CatalogEntry("site", 5, "dev_export"),
    "T06": CatalogEntry("site", 10, "dev_export"),
    "T07": CatalogEntry("site", 5, "dev_export"),
    "T08": CatalogEntry("site", 5, "dev_export"),
    "T09": CatalogEntry("site", 10, "generate"),
    "L01": CatalogEntry("info", 30, "owner_action"),
    "L02": CatalogEntry("info", 70, "owner_action"),
    "M01": CatalogEntry("mentiuni", 45, "owner_action"),
    "M02": CatalogEntry("mentiuni", 25, "owner_action"),
    "M03": CatalogEntry("mentiuni", 15, "generate"),
    "M05": CatalogEntry("mentiuni", 15, "owner_action"),
    "S01": CatalogEntry("social", 20, "owner_action"),
    "S02": CatalogEntry("social", 20, "owner_action"),
    "S03": CatalogEntry("social", 25, "generate"),
    "S04": CatalogEntry("social", 15, "owner_action"),
    "S05": CatalogEntry("social", 20, "generate"),
    "K01": CatalogEntry("cunoaste", 50, "owner_action"),
    "K02": CatalogEntry("cunoaste", 30, "owner_action"),
    "K03": CatalogEntry("cunoaste", 20, "owner_action"),
}
"""Every check: its chapter, points out of the chapter's 100 and fix type.

G01 is the profile gate: it is only reported when it fails, and then alone, so the chapter scores 0.
"""

STATUS_SHARE: dict[CheckStatus, float] = {"pass": 1.0, "partial": 0.5, "fail": 0.0, "unknown": 0.0}
"""The share of a check's points each status earns, unless the collector grades it more finely."""


def get_catalog_entry(check_id: str) -> CatalogEntry:
    """Returns the catalog entry of a check; per-field IDs like „L02:glovo:phone” use their base check."""
    return CATALOG[check_id.split(":")[0]]


def get_check_result(
    check_id: str,
    status: CheckStatus,
    evidence: Evidence | None = None,
    params: dict[str, str] | None = None,
    earned_share: float | None = None,
    points_max: float | None = None,
    gate: bool = False,
    reason_ro: str | None = None,
) -> CheckResult:
    """Returns a check result with points from the catalog: full for pass, half for partial, or `earned_share` of the maximum."""
    entry = get_catalog_entry(check_id)
    maximum = entry.points if points_max is None else points_max
    share = STATUS_SHARE[status] if earned_share is None else earned_share
    return CheckResult(
        check_id=check_id,
        chapter_id=entry.chapter_id,
        status=status,
        points_earned=maximum * share,
        points_max=maximum,
        gate=gate,
        evidence=evidence or Evidence(),
        params=params or {},
        reason_ro=reason_ro,
    )


def get_unknown_results(check_ids: list[str], reason_ro: str) -> list[CheckResult]:
    """Returns `unknown` results for checks that couldn't run, all with the same reason."""
    return [get_check_result(check_id, "unknown", reason_ro=reason_ro) for check_id in check_ids]


def get_earned(check: CheckResult) -> float:
    """Returns the points a check counts for: all of them once the owner marked it fixed."""
    return check.points_max if check.claimed_fixed else check.points_earned


def get_known_max(checks: list[CheckResult]) -> float:
    """Returns the sum of the maximum points of the checks that could run."""
    return sum(check.points_max for check in checks if check.status != "unknown")


def get_chapter_score(chapter_id: ChapterId, checks: list[CheckResult], all_checks: list[CheckResult]) -> int | None:
    """Returns a chapter's score over its known checks after the gates, or `None` when no check could run."""
    known_max = get_known_max(checks)
    if known_max == 0:
        return None
    score = round(100 * sum(get_earned(check) for check in checks if check.status != "unknown") / known_max)
    gate_open = any(check.gate and not check.claimed_fixed for check in all_checks if check.chapter_id == "site")
    if chapter_id == "continut" and gate_open:
        return min(score, CONTINUT_GATE_CAP)
    return score


def get_problem_points(check: CheckResult, checks: list[CheckResult]) -> int:
    """Returns how much the chapter score would rise if this check were fixed."""
    known_max = get_known_max(checks)
    if known_max == 0:
        return 0
    return round(100 * (check.points_max - check.points_earned) / known_max)


def get_overall_exact(chapter_scores: dict[ChapterId, int | None], gemini_score: int | None) -> float:
    """Returns the weighted mean of the known chapter scores and the Gemini score, renormalized over the known weights."""
    weighted = [(CHAPTER_WEIGHTS[chapter_id], score) for chapter_id, score in chapter_scores.items() if score is not None]
    if gemini_score is not None:
        weighted.append((GEMINI_WEIGHT, gemini_score))
    total_weight = sum(weight for weight, _ in weighted)
    if total_weight == 0:
        return 0.0
    return round(sum(weight * score for weight, score in weighted) / total_weight, 2)


def get_known_weight(report: Report) -> float:
    """Returns the sum of the weights of the chapters and Gemini test that have a score."""
    total = sum(CHAPTER_WEIGHTS[chapter.id] for chapter in report.chapters if chapter.score is not None)
    if report.gemini.score is not None:
        total += GEMINI_WEIGHT
    return total


def get_chapter_impact(chapter: Chapter) -> float:
    """Returns the overall points the chapter's open problems are worth together."""
    return sum(problem.impact for problem in chapter.problems)


def refresh_report_totals(report: Report) -> None:
    """Recomputes every number derived from the chapter scores and open problems, from the overall score to where to start."""
    report.overall_exact = get_overall_exact(
        {chapter.id: chapter.score for chapter in report.chapters},
        report.gemini.score,
    )
    report.overall = round(report.overall_exact)
    known_weight = get_known_weight(report)
    for chapter in report.chapters:
        chapter.problems.sort(key=lambda problem: problem.points, reverse=True)
        chapter.possible_points = sum(problem.points for problem in chapter.problems)
        overall_gain = chapter.possible_points * CHAPTER_WEIGHTS[chapter.id] / known_weight if known_weight else 0
        chapter.overall_gain_if_all_fixed = round(overall_gain)
    open_problems: list[Problem] = [problem for chapter in report.chapters for problem in chapter.problems]
    report.open_problem_count = len(open_problems)
    report.next_steps = sorted(open_problems, key=lambda problem: problem.impact, reverse=True)[:NEXT_STEPS_COUNT]
    chapters_with_problems = [chapter for chapter in report.chapters if chapter.problems]
    start_chapter = max(chapters_with_problems, key=get_chapter_impact, default=None)
    report.start_here = start_chapter.id if start_chapter else None
    for chapter in report.chapters:
        chapter.start_here = chapter.id == report.start_here
