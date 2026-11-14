import Link from "next/link";
import { chapterIconPath, Icon } from "@/components/Icon";
import { ScoreRing } from "@/components/ScoreRing";
import { getProblemCountLabel } from "@/lib/format";
import { type Chapter, isChapterSolved } from "@/lib/types";

/** A component that lists the chapters as cards on mobile. */
export function ChapterGrid({ scanId, chapters }: { scanId: string; chapters: Chapter[] }) {
  return (
    <section aria-labelledby="chapters-title" className="flex flex-col gap-3.5 pt-2 lg:hidden">
      <h2 id="chapters-title" className="mx-1 text-xl font-extrabold">
        Capitole
      </h2>
      <div className="grid grid-cols-2 gap-3 pt-2">
        {chapters.map((chapter) => (
          <ChapterCard key={chapter.id} href={`/scan/${scanId}/${chapter.id}`} chapter={chapter} />
        ))}
      </div>
    </section>
  );
}

/** Returns the status line of a chapter card. */
function getChapterStatus(chapter: Chapter): string {
  if (!chapter.has_fixes) {
    return "Crește pe măsură ce rezolvi restul";
  }
  if (isChapterSolved(chapter)) {
    return "Totul rezolvat";
  }
  if (chapter.problems.length === 0) {
    return "Nu am putut verifica";
  }
  return `${getProblemCountLabel(chapter.problems.length)} de rezolvat`;
}

/** A component that shows one chapter's icon, score ring, name and status as a link. */
function ChapterCard({ href, chapter }: { href: string; chapter: Chapter }) {
  return (
    <Link href={href} className="flex min-h-41 flex-col gap-2.5 rounded-[22px] border border-border bg-surface p-4 text-ink">
      <div className="flex items-start justify-between">
        <span className="flex size-9 items-center justify-center rounded-xl bg-fill text-accent">
          <Icon path={chapterIconPath[chapter.id]} size={19} />
        </span>
        <ScoreRing score={chapter.score} size={52} />
      </div>
      <span className="text-sm leading-[1.3] font-bold">{chapter.name_ro}</span>
      <span className={`mt-auto text-xs leading-[1.35] font-semibold ${chapter.has_fixes ? "text-body" : "text-muted"}`}>
        {getChapterStatus(chapter)}
      </span>
    </Link>
  );
}
