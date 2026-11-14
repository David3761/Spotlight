import type { Chapter, ChapterId, Message, Report } from "@/lib/types";

/** A problem the owner marked as fixed in the open conversation. */
export interface ConfirmedItem {
  /** The check's ID. */
  checkId: string;
  /** The problem's title. */
  title: string;
  /** The points it added. */
  points: number;
  /** The chapter the check belongs to, or `null` when the report doesn't know it. */
  chapterId: ChapterId | null;
}

/** A line of the chapter's task list in the side panel. */
export interface ChapterTask {
  /** The check's ID. */
  checkId: string;
  /** The problem's title. */
  title: string;
  /** The points it adds. */
  points: number;
  /** When `true`, the owner marked it fixed in this conversation. */
  isDone: boolean;
}

/** Returns the chapter a check belongs to, whether it's still open or already solved. */
export function getChapterOfCheck(report: Report, checkId: string): Chapter | null {
  return (
    report.chapters.find(
      (chapter) =>
        chapter.problems.some((problem) => problem.check_id === checkId) ||
        chapter.solved.some((solved) => solved.check_id === checkId),
    ) ?? null
  );
}

/** Returns the problems confirmed by the conversation's actions, in the order they were confirmed. */
export function getConfirmedItems(report: Report, messages: Message[]): ConfirmedItem[] {
  return messages.flatMap((message) => {
    const action = message.action;
    if (action?.status !== "confirmed") {
      return [];
    }
    return action.items
      .filter((item) => (action.confirmed_check_ids ?? []).includes(item.check_id))
      .map((item) => ({
        checkId: item.check_id,
        title: item.title_ro,
        points: item.points,
        chapterId: getChapterOfCheck(report, item.check_id)?.id ?? null,
      }));
  });
}

/** Returns the chapter the side panel shows: the conversation's, else the one of the last confirmed item. */
export function getPanelChapter(report: Report, chapterId: ChapterId | null, confirmedItems: ConfirmedItem[]): Chapter | null {
  const panelChapterId = chapterId ?? confirmedItems[confirmedItems.length - 1]?.chapterId ?? null;
  return report.chapters.find((chapter) => chapter.id === panelChapterId) ?? null;
}

/** Returns the chapter's open problems plus the items confirmed in the conversation, most points first. */
export function getChapterTasks(chapter: Chapter, confirmedItems: ConfirmedItem[]): ChapterTask[] {
  const open = chapter.problems.map((problem) => ({
    checkId: problem.check_id,
    title: problem.title_ro,
    points: problem.points,
    isDone: false,
  }));
  const done = confirmedItems
    .filter((item) => item.chapterId === chapter.id && !open.some((task) => task.checkId === item.checkId))
    .map((item) => ({ checkId: item.checkId, title: item.title, points: item.points, isDone: true }));
  return [...open, ...done].sort((first, second) => second.points - first.points);
}
