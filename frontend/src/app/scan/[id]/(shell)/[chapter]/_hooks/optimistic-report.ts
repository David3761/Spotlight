import type { Chapter, Problem, Report } from "@/lib/types";

/** Returns the chapter with a problem moved to its solved items and every derived number recomputed. */
function getChapterWithFix(chapter: Chapter, problem: Problem): Chapter {
  const problems = chapter.problems.filter((item) => item.check_id !== problem.check_id);
  return {
    ...chapter,
    score: Math.min(100, (chapter.score ?? 0) + problem.points),
    possible_points: problems.reduce((sum, item) => sum + item.points, 0),
    overall_gain_if_all_fixed: Math.round(problems.reduce((sum, item) => sum + item.impact, 0)),
    problems,
    solved: [
      ...chapter.solved,
      { check_id: problem.check_id, title_ro: problem.title_ro, source: "claimed_fixed", points: problem.points },
    ],
  };
}

/** Returns the report as it would look once the problem is marked fixed; unchanged when the problem isn't open. */
export function getOptimisticReport(report: Report, checkId: string): Report {
  const problem = report.chapters.flatMap((chapter) => chapter.problems).find((item) => item.check_id === checkId);
  if (!problem) {
    return report;
  }
  const chapters = report.chapters.map((chapter) =>
    chapter.id === problem.chapter_id ? getChapterWithFix(chapter, problem) : chapter,
  );
  const openProblems = chapters.flatMap((chapter) => chapter.problems);
  const overallExact = Math.min(100, report.overall_exact + problem.impact);
  return {
    ...report,
    chapters,
    overall_exact: overallExact,
    overall: Math.round(overallExact),
    open_problem_count: openProblems.length,
    next_steps: [...openProblems].sort((first, second) => second.impact - first.impact).slice(0, 3),
  };
}
