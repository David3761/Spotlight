"""Scores: chapter weights, the overall score and the totals derived from open problems."""

from app.models import Chapter, ChapterId, Problem, Report

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
