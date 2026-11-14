import { PointsBadge } from "@/components/PointsBadge";
import type { Problem } from "@/lib/types";

/** A component that shows an open problem with its points and a button that opens its fix. */
export function ProblemCard({ problem, onOpen }: { problem: Problem; onOpen: (checkId: string) => void }) {
  return (
    <article className="flex flex-col gap-3 rounded-[22px] border border-border bg-surface p-4 lg:flex-row lg:items-center lg:gap-4.5 lg:rounded-3xl lg:px-5.5 lg:py-5">
      <div className="flex min-w-0 items-start gap-3 lg:flex-1 lg:items-center lg:gap-4.5">
        <PointsBadge points={problem.points} size="responsive" />
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <h3 className="text-[15px] leading-[1.35] font-bold lg:text-[17px]">{problem.title_ro}</h3>
          <p className="text-[13px] leading-normal text-subtle lg:text-sm lg:leading-[1.55]">{problem.why_ro}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={() => onOpen(problem.check_id)}
        className="h-11.5 w-full shrink-0 rounded-full bg-accent text-[15px] font-bold text-white hover:bg-accent-hover lg:w-auto lg:px-6"
      >
        Rezolvă
      </button>
    </article>
  );
}
