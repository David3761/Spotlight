"use client";

import { useState } from "react";
import { Icon, iconPath } from "@/components/Icon";
import type { SolvedItem } from "@/lib/types";

/** A component that lists the solved checks; collapsible unless `isOpenAlways` is `true`. */
export function SolvedList({ items, isOpenAlways }: { items: SolvedItem[]; isOpenAlways: boolean }) {
  const [isOpen, setIsOpen] = useState(false);
  const isShown = isOpenAlways || isOpen;
  const heading = (
    <>
      <span className="flex size-6.5 items-center justify-center rounded-full bg-high text-white lg:size-7">
        <Icon path={iconPath.check} size={14} strokeWidth={3} />
      </span>
      <span className="flex-1 text-[15px] font-bold lg:text-base">Rezolvate · {items.length}</span>
    </>
  );

  return (
    <section aria-label="Rezolvate" className="overflow-hidden rounded-[22px] border border-border bg-surface lg:rounded-3xl">
      {isOpenAlways ? (
        <div className="flex min-h-13 items-center gap-3 px-4 pt-2 lg:px-5.5">{heading}</div>
      ) : (
        <button
          type="button"
          aria-expanded={isOpen}
          onClick={() => setIsOpen(!isOpen)}
          className="flex min-h-14 w-full items-center gap-3 px-4 text-start lg:min-h-15 lg:px-5.5"
        >
          {heading}
          <Icon
            path={iconPath.chevronDown}
            size={20}
            className={`text-subtle transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          />
        </button>
      )}
      {isShown && (
        <ul className="px-4 pb-2.5 lg:px-5.5 lg:pb-3.5">
          {items.map((item) => (
            <li
              key={item.check_id}
              className="flex items-center gap-2.5 border-t border-fill py-2.75 text-sm font-semibold text-subtle lg:gap-3 lg:py-3 lg:text-[15px]"
            >
              <Icon path={iconPath.check} size={20} strokeWidth={2.6} className="shrink-0 text-high-text" />
              <span className="min-w-0 flex-1">{item.title_ro}</span>
              {item.source === "claimed_fixed" && item.points !== null && (
                <span className="text-[13px] font-bold text-high-text">+{item.points}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
