"use client";

import { BackLink } from "@/components/BackLink";
import { buttonVariant } from "@/components/button-styles";
import { Icon, iconPath } from "@/components/Icon";
import { ScoreRing } from "@/components/ScoreRing";
import { useIsDesktop } from "@/hooks/use-is-desktop";
import { getProblemCountLabel } from "@/lib/format";
import type { Chapter } from "@/lib/types";
import { screenIconPath } from "./icons";

/** A component that shows the back link and the chapter's ring, name, intro and points; smaller once everything is solved. */
export function ChapterHeader({
  scanId,
  chapter,
  isDone,
  googleMapsUri,
}: {
  scanId: string;
  chapter: Chapter;
  isDone: boolean;
  googleMapsUri: string | null;
}) {
  const isDesktop = useIsDesktop();
  const ringSize = isDesktop ? (isDone ? 120 : 180) : 160;
  const ringThick = isDesktop ? (isDone ? 14 : 18) : 16;
  const showsPoints = chapter.has_fixes && !isDone;

  return (
    <>
      <BackLink scanId={scanId} />

      <section className="flex flex-col items-center gap-3.5 px-5 pt-1 pb-5 text-center lg:flex-row lg:flex-wrap lg:gap-8 lg:rounded-[28px] lg:border lg:border-border lg:bg-surface lg:p-8 lg:text-start lg:shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_rgba(15,23,42,0.05)]">
        <ScoreRing score={chapter.score} size={ringSize} thick={ringThick} />
        <div className="flex flex-col items-center gap-3 lg:min-w-80 lg:flex-1 lg:items-start">
          <span className="hidden text-xs font-bold tracking-[0.08em] text-muted uppercase lg:block">Capitol</span>
          <h1 className="text-[26px] font-extrabold tracking-[-0.02em] lg:text-[32px]">{chapter.name_ro}</h1>
          {showsPoints && (
            <div className="flex flex-wrap justify-center gap-2 lg:order-last lg:justify-start">
              <span className="flex h-8 items-center gap-1.5 rounded-full bg-high-tint px-3.5 text-sm font-extrabold text-high-text lg:h-8.5">
                <Icon path={iconPath.arrowUp} size={15} strokeWidth={2.6} />+{chapter.possible_points} puncte posibile
              </span>
              <span className="hidden h-8.5 items-center rounded-full bg-fill px-3.5 text-sm font-bold text-body lg:flex">
                {getProblemCountLabel(chapter.problems.length)} de rezolvat
              </span>
            </div>
          )}
          <p className="max-w-140 text-sm leading-[1.55] text-subtle lg:text-base">{chapter.intro_ro}</p>
        </div>
        {googleMapsUri && chapter.id === "profil" && (
          <a
            href={googleMapsUri}
            target="_blank"
            rel="noopener noreferrer"
            className={`${buttonVariant.outline} h-12 w-full px-5 text-[15px] lg:w-auto`}
          >
            Deschide Profilul tău Google
            <Icon path={screenIconPath.external} size={16} strokeWidth={2.2} />
          </a>
        )}
      </section>
    </>
  );
}
