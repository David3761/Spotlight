"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { Icon, iconPath } from "@/components/Icon";
import { ScoreRing } from "@/components/ScoreRing";
import type { GeminiBlock } from "@/lib/types";
import { getDayLabel } from "./format";

/** How many competitors the card lists. */
const COMPETITOR_LIMIT = 3;

/** A component that links to the Gemini screen with the live-test score and the top competitors. */
export function GeminiCard({ scanId, gemini }: { scanId: string; gemini: GeminiBlock }) {
  const isUnknown = gemini.status === "unknown";
  const summary = isUnknown ? "Nu am putut rula testul" : `Apari în ${gemini.mentioned} din ${gemini.total} răspunsuri`;
  const competitors = isUnknown ? [] : gemini.top_competitors.slice(0, COMPETITOR_LIMIT);

  return (
    <Link
      href={`/scan/${scanId}/gemini`}
      aria-label={`Vizibilitate în Gemini: ${summary.toLowerCase()}. Vezi detaliile.`}
      className="flex min-w-0 flex-col gap-4 rounded-[28px] border-2 border-accent-outline bg-accent-soft p-5 text-ink lg:flex-[1_1_380px] lg:gap-4.5 lg:p-7"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="flex h-7 items-center gap-2 rounded-full bg-surface px-3 text-xs font-bold text-accent-strong lg:h-7.5">
          <motion.span
            aria-hidden="true"
            className="size-2 rounded-full bg-accent"
            animate={{ opacity: [1, 0.35, 1], scale: [1, 0.7, 1] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          />
          {isUnknown ? "Test real" : `Test real · ${getDayLabel(gemini.last_checked)}`}
        </span>
        <span className="hidden items-center gap-1 text-sm font-bold text-accent-hover lg:flex">
          Vezi răspunsurile
          <Icon path={iconPath.chevronRight} size={16} strokeWidth={2.2} />
        </span>
        <Icon path={iconPath.chevronRight} size={20} strokeWidth={2.2} className="text-accent-hover lg:hidden" />
      </div>
      <div className="flex items-center gap-4 lg:gap-5">
        <span className="lg:hidden">
          <ScoreRing score={gemini.score} size={76} />
        </span>
        <span className="hidden lg:block">
          <ScoreRing score={gemini.score} size={96} />
        </span>
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-lg font-extrabold lg:text-xl lg:tracking-[-0.01em]">Vizibilitate în Gemini</span>
          <span className="text-sm font-semibold text-accent-deep lg:text-base">{summary}</span>
        </div>
      </div>
      {competitors.length > 0 && (
        <div className="flex flex-col gap-2.5 rounded-[18px] bg-surface px-3.5 py-3 lg:rounded-[20px] lg:px-4 lg:py-3.5">
          <span className="text-xs font-semibold text-subtle lg:text-[13px]">În locul tău, Gemini recomandă:</span>
          {competitors.map((competitor, index) => (
            <div key={competitor.name} className="flex items-center gap-2.5">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-lg bg-fill text-xs font-extrabold text-subtle lg:size-6.5 lg:rounded-[9px] lg:text-[13px]">
                {index + 1}
              </span>
              <span className="min-w-0 flex-1 text-sm font-bold lg:text-[15px]">{competitor.name}</span>
              <span className="text-xs font-semibold text-muted lg:text-[13px]">
                <span className="hidden lg:inline">în {competitor.mentions} răspunsuri</span>
                <span className="lg:hidden">
                  {competitor.mentions} din {gemini.total}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}
