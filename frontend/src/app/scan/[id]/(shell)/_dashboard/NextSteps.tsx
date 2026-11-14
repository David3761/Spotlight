import Link from "next/link";
import { buttonVariant } from "@/components/button-styles";
import { PointsBadge } from "@/components/PointsBadge";
import type { Problem } from "@/lib/types";

/** A component that lists the open problems worth the most points, each linking to its fix. */
export function NextSteps({ scanId, problems }: { scanId: string; problems: Problem[] }) {
  if (problems.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="next-steps-title"
      className="flex min-w-0 flex-[1.6_1_460px] flex-col gap-1.5 rounded-[28px] border border-border bg-surface px-7 py-6.5"
    >
      <div className="flex items-baseline justify-between gap-3 pb-2">
        <h2 id="next-steps-title" className="text-xl font-extrabold">
          Următorii pași
        </h2>
        <span className="text-[13px] font-semibold text-muted">Cele care îți aduc cele mai multe puncte</span>
      </div>
      {problems.map((problem) => (
        <div key={problem.check_id} className="flex items-center gap-4 border-t border-fill py-3.5">
          <PointsBadge points={problem.points} size="fixed" />
          <span className="flex min-w-0 flex-1 flex-col gap-0.75">
            <span className="text-base font-bold">{problem.title_ro}</span>
            <span className="text-[13px] font-semibold text-muted">{problem.chapter_name_ro}</span>
          </span>
          <Link
            href={`/scan/${scanId}/${problem.chapter_id}?fix=${problem.check_id}`}
            className={`${buttonVariant.primary} h-11 px-5 text-sm`}
          >
            Rezolvă
          </Link>
        </div>
      ))}
    </section>
  );
}
