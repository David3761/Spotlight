import Link from "next/link";
import { buttonVariant } from "@/components/button-styles";
import { Icon } from "@/components/Icon";
import { ScoreRing } from "@/components/ScoreRing";
import type { Report } from "@/lib/types";
import { getProblemCountLabel } from "./format";

/** The path of the arrow icon. */
const arrowPath = "M5 12h14M13 6l6 6-6 6";

/** The look shared by the summary chips. */
const chipClass = "h-7.5 items-center rounded-full bg-fill px-3 text-[13px] font-bold text-body lg:h-8";

/** A component that shows the overall score ring, the progress line, the counts and the start button. */
export function OverallCard({ report }: { report: Report }) {
  const startChapter = report.chapters.find((chapter) => chapter.id === report.start_here);

  return (
    <section
      aria-label="Scor general"
      className="flex min-w-0 flex-col items-center gap-4 rounded-[28px] border border-border bg-surface px-5 py-6 text-center shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_rgba(15,23,42,0.05)] lg:flex-[1.2_1_460px] lg:flex-row lg:flex-wrap lg:gap-8 lg:p-8 lg:text-start"
    >
      <span className="order-first text-xs font-bold tracking-[0.08em] text-muted uppercase lg:hidden">Scor general</span>
      <span className="lg:hidden">
        <ScoreRing score={report.overall} size={168} thick={18} showMax />
      </span>
      <span className="hidden lg:block">
        <ScoreRing score={report.overall} size={200} thick={20} showMax />
      </span>
      <div className="contents lg:flex lg:flex-[1_1_240px] lg:flex-col lg:gap-3.5">
        <span className="hidden text-xs font-bold tracking-[0.08em] text-muted uppercase lg:block">Scor general</span>
        <p className="hidden text-[22px] leading-[1.35] font-bold tracking-[-0.01em] lg:block">
          Progres înspre a fi mai vizibil
        </p>
        <p className="text-[17px] leading-[1.4] font-bold lg:hidden">{report.summary_ro}</p>
        <div className="flex flex-wrap justify-center gap-2 lg:justify-start">
          <span className={`flex ${chipClass}`}>{getProblemCountLabel(report.open_problem_count)} de rezolvat</span>
          <span className={`hidden lg:flex ${chipClass}`}>{report.chapters.length} capitole</span>
        </div>
        {startChapter && (
          <Link
            href={`/scan/${report.scan_id}/${startChapter.id}`}
            className={`${buttonVariant.primary} h-12.5 w-full text-[15px] lg:h-12 lg:w-auto lg:self-start lg:px-5.5`}
          >
            Începe cu {startChapter.name_ro}
            <Icon path={arrowPath} size={18} strokeWidth={2.2} className="hidden lg:block" />
          </Link>
        )}
      </div>
    </section>
  );
}
