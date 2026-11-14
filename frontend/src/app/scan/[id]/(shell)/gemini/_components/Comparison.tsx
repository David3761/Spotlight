import Link from "next/link";
import {
  getComparisonRows,
  getCountText,
  getRatingRangeText,
  type ComparisonTag,
  type TagTone,
} from "./comparison-rows";
import type { CompareRow, Comparison as ComparisonData } from "@/lib/types";

/** The pill colours of each tag tone. */
const tagPillClass: Record<TagTone, string> = {
  low: "bg-low-tint text-low-text",
  mid: "bg-mid-tint text-mid-text",
  high: "bg-high-tint text-high-text",
};

/** The text colours of each tag tone, for the mobile summary cards. */
const tagTextClass: Record<TagTone, string> = {
  low: "text-low-text",
  mid: "text-mid-text",
  high: "text-high-text",
};

/** The props of {@link Comparison}. */
interface ComparisonProps {
  /** The scan's ID. */
  scanId: string;
  /** The comparison with the most recommended competitors. */
  comparison: ComparisonData;
}

/** A component that compares the business with the competitors Gemini recommends most, with the conclusions and fixes. */
export function Comparison({ scanId, comparison }: ComparisonProps) {
  const { me, rivals, insights_ro: insights, actions } = comparison;
  const [reviewsRow, ratingRow, photosRow, hoursRow] = getComparisonRows(me, rivals);
  const rows = [reviewsRow, ratingRow, photosRow, hoursRow];
  const ratingRange = getRatingRangeText(rivals);
  const hasConclusions = insights.length > 0 || actions.length > 0;
  const firstAction = actions[0];

  return (
    <section
      aria-labelledby="comparison-title"
      className="flex flex-col gap-4.5 rounded-[22px] border border-border bg-surface px-4 py-4.5 lg:gap-5 lg:rounded-[28px] lg:px-8 lg:py-7"
    >
      <div className="flex flex-col gap-1 lg:flex-row lg:flex-wrap lg:items-baseline lg:justify-between lg:gap-2">
        <h2 id="comparison-title" className="text-lg font-extrabold lg:text-[22px] lg:tracking-[-0.01em]">
          De ce îi alege Gemini pe ei?
        </h2>
        <span className="text-[13px] text-muted lg:text-sm">
          <span className="lg:hidden">Tu față de cele {rivals.length} afaceri recomandate cel mai des</span>
          <span className="hidden lg:inline">
            {me.name} față de cele {rivals.length} afaceri recomandate cel mai des
          </span>
        </span>
      </div>

      <div className="hidden overflow-x-auto lg:block">
        <table className="w-full min-w-190 border-separate border-spacing-0 text-[15px]">
          <thead>
            <tr>
              <th scope="col" className="px-4 py-3 text-start text-[13px] font-bold text-muted">
                Ce contează
              </th>
              <th
                scope="col"
                className="rounded-t-2xl bg-accent-soft px-4 py-3 text-start text-sm font-extrabold text-accent-strong"
              >
                {me.name}
              </th>
              {rivals.map((rival, index) => (
                <th key={`${rival.name}-${index}`} scope="col" className="px-4 py-3 text-start text-sm font-bold">
                  {rival.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row.label}>
                <th scope="row" className="border-t border-fill p-4 text-start text-sm font-semibold text-body">
                  {row.label}
                </th>
                <td
                  className={`border-t border-accent-tint bg-accent-soft p-4 ${rowIndex === rows.length - 1 ? "rounded-b-2xl" : ""}`}
                >
                  <span className="flex flex-wrap items-center gap-2.5">
                    <span className="text-[17px] font-extrabold">{row.me}</span>
                    {row.tag && <TagPill tag={row.tag} />}
                  </span>
                </td>
                {row.rivals.map((value, rivalIndex) => (
                  <td key={`${row.label}-${rivalIndex}`} className="border-t border-fill p-4 font-bold">
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-4.5 lg:hidden">
        <CountBars label="Recenzii pe Google" tag={reviewsRow.tag} me={me} rivals={rivals} field="review_count" />
        <CountBars label="Fotografii" tag={photosRow.tag} me={me} rivals={rivals} field="photo_count" />
        <div className="grid grid-cols-2 gap-2.5">
          <div className="flex flex-col gap-1 rounded-2xl bg-page p-3">
            <span className="text-xs font-semibold text-muted">Notă medie</span>
            <span className="text-xl font-extrabold">{ratingRow.me}</span>
            {ratingRow.tag && ratingRange && (
              <span className={`text-xs font-bold ${tagTextClass[ratingRow.tag.tone]}`}>la fel ca ei ({ratingRange})</span>
            )}
          </div>
          <div className="flex flex-col gap-1 rounded-2xl bg-page p-3">
            <span className="text-xs font-semibold text-muted">Program complet</span>
            <span className="text-xl font-extrabold">{hoursRow.me}</span>
            {hoursRow.tag && <span className={`text-xs font-bold ${tagTextClass[hoursRow.tag.tone]}`}>ei toți îl au</span>}
          </div>
        </div>
      </div>

      <div
        className={`flex flex-col gap-4.5 lg:flex-row lg:flex-wrap lg:items-center lg:gap-4 ${
          hasConclusions ? "lg:rounded-[20px] lg:bg-page lg:px-5 lg:py-4.5" : ""
        }`}
      >
        {insights.length > 0 && (
          <div className="flex flex-col gap-2 lg:flex-1 lg:basis-85">
            {insights.map((insight) => (
              <p key={insight} className="text-sm leading-normal text-body lg:text-[15px] lg:leading-[1.55]">
                {insight}
              </p>
            ))}
          </div>
        )}
        {actions.length > 0 && (
          <div className="hidden flex-wrap gap-2 lg:flex">
            {actions.map((action) => (
              <Link
                key={action.check_id}
                href={`/scan/${scanId}/${action.chapter_id}?fix=${action.check_id}`}
                className="flex h-11 items-center rounded-full border border-accent-outline bg-surface px-4 text-sm font-bold text-accent-strong"
              >
                {action.label_ro}
              </Link>
            ))}
          </div>
        )}
        <Link
          href={firstAction ? `/scan/${scanId}/${firstAction.chapter_id}` : `/scan/${scanId}`}
          className="flex h-12 items-center justify-center rounded-full bg-accent-soft text-[15px] font-bold text-accent-strong lg:hidden"
        >
          Vezi ce poți rezolva acum
        </Link>
      </div>
    </section>
  );
}

/** A component that shows a short verdict as a pill. */
function TagPill({ tag }: { tag: ComparisonTag }) {
  return (
    <span className={`flex h-6 items-center rounded-full px-2.5 text-xs font-bold ${tagPillClass[tag.tone]}`}>{tag.text}</span>
  );
}

/** The props of {@link CountBars}. */
interface CountBarsProps {
  /** The metric's label. */
  label: string;
  /** The verdict next to the label; `null` for none. */
  tag: ComparisonTag | null;
  /** The owner's business. */
  me: CompareRow;
  /** The competitors. */
  rivals: CompareRow[];
  /** Which count the bars show. */
  field: "review_count" | "photo_count";
}

/** A component that shows one count of the owner and the competitors as horizontal bars. */
function CountBars({ label, tag, me, rivals, field }: CountBarsProps) {
  const businesses = [me, ...rivals];
  const max = Math.max(...businesses.map((business) => business[field] ?? 0));

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold">{label}</span>
        {tag && (
          <span className={`flex h-5.5 items-center rounded-full px-2 text-[11px] font-bold ${tagPillClass[tag.tone]}`}>
            {tag.text}
          </span>
        )}
      </div>
      {businesses.map((business, index) => {
        const value = business[field] ?? 0;
        const width = max > 0 ? Math.max(3, Math.round((value / max) * 100)) : 3;
        const isMe = index === 0;
        return (
          <div key={`${business.name}-${index}`} className="flex items-center gap-2">
            <span
              className={`w-28 flex-none text-xs ${isMe ? "font-extrabold text-accent-strong" : "font-semibold text-subtle"}`}
            >
              {business.name}
            </span>
            <span className="h-2.5 flex-1 overflow-hidden rounded-[5px] bg-fill">
              <span
                className={`block h-2.5 rounded-[5px] ${isMe ? "bg-accent" : "bg-bar"}`}
                style={{ width: `${width}%` }}
              />
            </span>
            <span className="w-9 text-end text-[13px] font-extrabold tabular-nums">
              {getCountText(business[field], field === "photo_count" && business.photo_count_capped)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
