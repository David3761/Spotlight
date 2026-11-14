import Link from "next/link";
import { buttonVariant } from "@/components/button-styles";
import { Icon, iconPath } from "@/components/Icon";
import type { Chapter } from "@/lib/types";

/** A component that celebrates a chapter with every problem solved and points on to what is left. */
export function ChapterDone({
  scanId,
  solvedCount,
  nextChapter,
}: {
  scanId: string;
  solvedCount: number;
  nextChapter: Chapter | null;
}) {
  return (
    <section
      aria-live="polite"
      className="flex flex-col items-center gap-5 rounded-[32px] border border-border bg-surface px-6 py-10 text-center lg:px-10 lg:py-14"
    >
      <div className="relative size-38">
        <svg width="152" height="152" viewBox="0 0 152 152" aria-hidden="true" className="absolute inset-0">
          <circle cx="76" cy="76" r="64" className="fill-high-tint" />
          <path d="M28 30l2.4 6.8L37 39l-6.6 2.4L28 48l-2.4-6.6L19 39l6.6-2.2z" className="fill-mid" />
          <path d="M126 22l1.8 5L133 29l-5.2 1.8L126 36l-1.8-5.2L119 29l5.2-2z" className="fill-accent" />
          <path d="M132 112l1.6 4.4 4.4 1.6-4.4 1.6-1.6 4.4-1.6-4.4-4.4-1.6 4.4-1.6z" className="fill-high" />
          <circle cx="22" cy="104" r="5" className="fill-accent-line" />
        </svg>
        <div className="absolute start-9 top-9 flex size-20 items-center justify-center rounded-full bg-high text-white shadow-[0_12px_28px_rgba(47,179,110,0.35)]">
          <Icon path={iconPath.check} size={40} strokeWidth={3} />
        </div>
      </div>
      <h2 className="text-[26px] font-extrabold tracking-[-0.02em] lg:text-3xl">Totul e rezolvat aici 🎉</h2>
      <p className="max-w-130 text-base leading-[1.55] text-subtle">
        Ai rezolvat toate cele {solvedCount} probleme din acest capitol.
      </p>
      <div className="mt-2 flex flex-wrap justify-center gap-3">
        {nextChapter && (
          <Link href={`/scan/${scanId}/${nextChapter.id}`} className={`${buttonVariant.primary} h-12.5 px-6 text-[15px]`}>
            Mergi la {nextChapter.name_ro}
            <Icon path={iconPath.arrowRight} size={18} strokeWidth={2.2} />
          </Link>
        )}
        <Link href={`/scan/${scanId}`} className={`${buttonVariant.outline} h-12.5 px-6 text-[15px]`}>
          Înapoi la panou
        </Link>
      </div>
    </section>
  );
}
