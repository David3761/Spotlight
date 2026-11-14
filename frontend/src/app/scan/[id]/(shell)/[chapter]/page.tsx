"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ErrorState } from "@/components/ErrorState";
import { Toast } from "@/components/Toast";
import { useLoadedScan } from "@/components/ScanShell";
import { type Chapter, isChapterSolved } from "@/lib/types";
import { useFixPanel } from "./_hooks/use-fix-panel";
import { useResolveProblem } from "./_hooks/use-resolve-problem";
import { ChapterDone } from "./_components/ChapterDone";
import { ChapterHeader } from "./_components/ChapterHeader";
import { FixPanel } from "./_components/FixPanel";
import { ProblemCard } from "./_components/ProblemCard";
import { AllFixedBox, WhereToFixBox } from "./_components/SideBoxes";
import { SolvedList } from "./_components/SolvedList";
import { UnknownList } from "./_components/UnknownList";

/** Returns the first chapter after the current one, wrapping around, that still has open problems. */
function getNextOpenChapter(chapters: Chapter[], currentId: string): Chapter | null {
  const currentIndex = chapters.findIndex((chapter) => chapter.id === currentId);
  const following = [...chapters.slice(currentIndex + 1), ...chapters.slice(0, currentIndex)];
  return following.find((chapter) => chapter.problems.length > 0) ?? null;
}

/** The chapter page: the chapter's score, its open problems with their fixes, and what is solved or unknown. */
export default function ChapterPage() {
  const { chapter: segment } = useParams<{ chapter: string }>();
  const router = useRouter();
  const { scanId, report, setReport } = useLoadedScan();
  const fixPanel = useFixPanel();
  const { toast, dismissToast, error, hasFailed, resolve, retry } = useResolveProblem(scanId, report, setReport);
  const chapter = report.chapters.find((item) => item.id === segment);

  useEffect(() => {
    if (!chapter) {
      router.replace(`/scan/${scanId}`);
    }
  }, [chapter, router, scanId]);

  if (!chapter) {
    return <div aria-busy="true" className="min-h-screen bg-page" />;
  }

  const openProblem = chapter.problems.find((problem) => problem.check_id === fixPanel.checkId) ?? null;
  const isDone = isChapterSolved(chapter);
  const hasProblems = chapter.problems.length > 0;
  const overallGain = chapter.overall_gain_if_all_fixed;

  return (
    <div className="flex flex-col gap-4 pb-6 lg:gap-6 lg:px-12 lg:pt-8 lg:pb-14">
      <ChapterHeader scanId={scanId} chapter={chapter} isDone={isDone} googleMapsUri={report.business.google_maps_uri} />

      {hasFailed && (
        <div className="px-4 lg:px-0">
          <ErrorState error={error} onRetry={retry} />
        </div>
      )}

      <div className="flex flex-col gap-6 px-4 lg:flex-row lg:items-start lg:px-0">
        <div className="flex min-w-0 flex-col gap-3 lg:flex-[999_1_520px] lg:gap-3.5">
          {isDone && <ChapterDone scanId={scanId} solvedCount={chapter.solved.length} nextChapter={getNextOpenChapter(report.chapters, chapter.id)} />}
          {hasProblems && (
            <>
              <div className="flex items-baseline justify-between gap-3 px-1">
                <h2 className="text-lg font-extrabold lg:text-xl">
                  De rezolvat<span className="lg:hidden"> · {chapter.problems.length}</span>
                </h2>
                <span className="hidden text-[13px] font-semibold text-muted lg:inline">
                  Cele care contează mai mult sunt primele
                </span>
              </div>
              {chapter.problems.map((problem) => (
                <ProblemCard key={problem.check_id} problem={problem} onOpen={fixPanel.open} />
              ))}
            </>
          )}
          {!chapter.has_fixes && (
            <div className="rounded-3xl border border-border bg-surface p-6 text-center">
              <p className="text-base font-bold text-ink">Crește pe măsură ce rezolvi restul</p>
            </div>
          )}
          {chapter.solved.length > 0 && <SolvedList items={chapter.solved} isOpenAlways={isDone} />}
          {chapter.unknown.length > 0 && <UnknownList items={chapter.unknown} />}
        </div>

        {(hasProblems || chapter.where_to_fix_ro) && (
          <aside className="flex flex-col gap-4 lg:max-w-95 lg:flex-[1_1_300px]">
            {hasProblems && (
              <AllFixedBox
                chapterScore={chapter.score}
                chapterScoreIfFixed={Math.min(100, (chapter.score ?? 0) + chapter.possible_points)}
                overall={report.overall}
                overallGain={overallGain}
              />
            )}
            {chapter.where_to_fix_ro && <WhereToFixBox text={chapter.where_to_fix_ro} />}
          </aside>
        )}
      </div>

      <FixPanel
        scanId={scanId}
        problem={openProblem}
        onClose={fixPanel.close}
        onResolve={(problem) => {
          fixPanel.close();
          void resolve(problem);
        }}
      />
      <Toast toast={toast} onDismiss={dismissToast} />
    </div>
  );
}
