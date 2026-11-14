import { Icon, iconPath } from "@/components/Icon";
import { InfoNote } from "@/components/InfoNote";
import { ScoreRing } from "@/components/ScoreRing";
import { getProblemCountLabel } from "@/lib/format";
import type { Chapter } from "@/lib/types";
import type { ChapterTask } from "./chat-data";

/** Returns how many problems a chapter has left, worded for the owner. */
function getRemainingLabel(remaining: number): string {
  return `${getProblemCountLabel(remaining)} ${remaining === 1 ? "rămasă" : "rămase"}`;
}

/** Returns the points the owner gained today in the tasks, i.e. those marked done. */
function getGainedPoints(tasks: ChapterTask[]): number {
  return tasks.filter((task) => task.isDone).reduce((sum, task) => sum + task.points, 0);
}

/** A component that shows, on mobile, the conversation's chapter ring with its remaining problems and points gained. */
export function ChapterStrip({ chapter, tasks }: { chapter: Chapter; tasks: ChapterTask[] }) {
  const gained = getGainedPoints(tasks);

  return (
    <div className="flex items-center gap-3 border-b border-divider bg-page px-4 py-2.5 lg:hidden">
      <ScoreRing score={chapter.score} size={44} animateFrom={getRingStart(chapter.score, gained)} />
      <span className="flex flex-1 flex-col gap-px">
        <span className="text-sm font-extrabold">{chapter.name_ro}</span>
        <span className="text-xs text-muted">{getRemainingLabel(chapter.problems.length)}</span>
      </span>
      {gained > 0 && <GainedPill points={gained} />}
    </div>
  );
}

/** Returns the score a ring starts from when it mounts after `gained` points were added. */
function getRingStart(score: number | null, gained: number): number | undefined {
  return score === null || gained === 0 ? undefined : Math.max(0, score - gained);
}

/** The props of {@link ChatPanel}. */
interface ChatPanelProps {
  /** The chapter to show; `null` hides the chapter card. */
  chapter: Chapter | null;
  /** The chapter's tasks. */
  tasks: ChapterTask[];
  /** The overall score now. */
  overall: number;
  /** The overall score when the conversation was opened. */
  overallAtOpen: number;
}

/** A component that shows, on desktop, the chapter ring and tasks, the overall ring and a footnote. */
export function ChatPanel({ chapter, tasks, overall, overallAtOpen }: ChatPanelProps) {
  const gained = getGainedPoints(tasks);

  return (
    <aside className="hidden max-w-90 flex-[1_1_300px] flex-col gap-4 lg:flex">
      {chapter && (
        <div className="flex flex-col gap-3.5 rounded-3xl border border-border bg-surface p-5.5">
          <div className="flex items-center gap-4">
            <ScoreRing score={chapter.score} size={96} animateFrom={getRingStart(chapter.score, gained)} />
            <div className="flex flex-col gap-1.5">
              <span className="text-[17px] font-extrabold">{chapter.name_ro}</span>
              {gained > 0 && <GainedPill points={gained} className="self-start" />}
              <span className="text-[13px] text-muted">{getRemainingLabel(chapter.problems.length)}</span>
            </div>
          </div>
          <ul className="flex flex-col">
            {tasks.map((task) => (
              <li key={task.checkId} className="flex items-center gap-2.5 border-t border-fill py-2.5">
                {task.isDone ? (
                  <span
                    role="img"
                    aria-label="Rezolvat"
                    className="flex size-5.5 flex-none items-center justify-center rounded-full bg-high text-white"
                  >
                    <Icon path={iconPath.check} size={12} strokeWidth={3.4} />
                  </span>
                ) : (
                  <span role="img" aria-label="De rezolvat" className="size-5.5 flex-none rounded-full border-2 border-bar" />
                )}
                <span className={`flex-1 text-[13px] leading-[1.35] font-semibold ${task.isDone ? "text-muted" : "text-ink"}`}>
                  {task.title}
                </span>
                <span className={`text-xs font-extrabold ${task.isDone ? "text-high-text" : "text-faint"}`}>+{task.points}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex items-center gap-3.5 rounded-3xl border border-border bg-surface px-5.5 py-4.5">
        <ScoreRing score={overall} size={60} animateFrom={overallAtOpen} />
        <div className="flex flex-col gap-0.5">
          <span className="text-[15px] font-extrabold">Scor general</span>
          <span className="text-[13px] text-muted">
            {overall === overallAtOpen ? `${overall} din 100` : `de la ${overallAtOpen} la ${overall} azi`}
          </span>
        </div>
      </div>
      <InfoNote isSmall>Asistentul marchează ceva ca rezolvat doar când îi spui tu, și poți anula oricând.</InfoNote>
    </aside>
  );
}

/** A component that shows the green pill with the points gained today. */
function GainedPill({ points, className = "" }: { points: number; className?: string }) {
  return (
    <span className={`flex h-6.5 items-center rounded-full bg-high-tint px-2.5 text-xs font-extrabold text-high-text ${className}`}>
      +{points} azi
    </span>
  );
}
