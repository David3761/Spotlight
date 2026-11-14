import type { UnknownItem } from "@/lib/types";

/** A component that lists the checks that couldn't run, each with the reason. */
export function UnknownList({ items }: { items: UnknownItem[] }) {
  return (
    <section
      aria-label="Nu am putut verifica"
      className="rounded-[22px] border border-border bg-surface px-4 py-4 lg:rounded-3xl lg:px-5.5 lg:py-5"
    >
      <h2 className="text-[15px] font-bold lg:text-base">Nu am putut verifica · {items.length}</h2>
      <ul className="mt-2 flex flex-col">
        {items.map((item) => (
          <li key={item.check_id} className="flex flex-col gap-0.5 border-t border-fill py-2.75 first:border-t-0">
            <span className="text-sm font-semibold text-ink">{item.title_ro}</span>
            <span className="text-[13px] leading-normal text-muted">{item.reason_ro}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
