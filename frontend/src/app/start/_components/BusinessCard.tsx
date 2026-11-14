"use client";

import { useState } from "react";
import { getInitials, stepCount, type Answers, type CardField } from "@/app/start/_hooks/onboarding-model";
import { Icon, iconPath } from "@/components/Icon";

/** The text colour of a card field's value for each status. */
const valueTone: Record<CardField["status"], string> = {
  done: "text-ink",
  active: "text-accent-hover",
  pending: "text-faint",
};

/** Returns the line under the business name, e.g. "Cafenea · Cotroceni, București". */
function getSubtitle(answers: Answers): string {
  const location = [answers.neighborhood, answers.city].filter(Boolean).join(", ");
  return [answers.typeLabel, location].filter(Boolean).join(" · ");
}

/** A component that shows the business card beside the chat on desktop, filling in as the owner answers. */
export function BusinessCard({
  answers,
  fields,
  doneCount,
}: {
  answers: Answers;
  fields: CardField[];
  doneCount: number;
}) {
  return (
    <aside aria-label="Cartea de vizită" className="hidden max-w-100 flex-1 basis-85 flex-col gap-4 lg:flex">
      <div className="flex flex-col gap-5.5 rounded-[28px] border border-border bg-surface p-7 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_rgba(15,23,42,0.05)]">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-bold tracking-[0.08em] text-muted uppercase">Cartea de vizită</span>
          <span className="text-[13px] text-muted">Se completează pe măsură ce răspunzi</span>
        </div>
        <div className="flex items-center gap-3.5">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-[18px] bg-accent-soft text-[19px] font-extrabold text-accent-strong">
            {getInitials(answers.businessName) || "?"}
          </div>
          <div className="flex min-w-0 flex-col gap-0.75">
            <span className="text-xl font-extrabold tracking-[-0.01em] wrap-break-word">
              {answers.businessName || "Afacerea ta"}
            </span>
            <span className="text-sm text-muted">{getSubtitle(answers) || "Urmează"}</span>
          </div>
        </div>
        <ul className="m-0 flex list-none flex-col gap-1 p-0">
          {fields.map((field) => (
            <li key={field.label} className="flex items-center gap-3 border-t border-fill py-2.5">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-fill text-subtle">
                <Icon path={field.icon} size={18} />
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="text-xs font-semibold text-muted">{field.label}</span>
                <span className={`text-sm font-semibold wrap-break-word ${valueTone[field.status]}`}>{field.value}</span>
              </span>
              <StatusDot status={field.status} />
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-2">
          <div className="text-[13px] font-semibold text-subtle">
            {doneCount} din {stepCount} gata
          </div>
          <div className="h-2 overflow-hidden rounded-sm bg-divider">
            <div className="h-2 rounded-sm bg-accent" style={{ width: `${(doneCount / stepCount) * 100}%` }} />
          </div>
        </div>
      </div>
      <p className="m-0 px-3 text-[13px] leading-normal text-muted">
        Poți schimba oricând orice răspuns din pagina afacerii tale.
      </p>
    </aside>
  );
}

/** A component that shows whether a card field is done, being answered or waiting. */
function StatusDot({ status }: { status: CardField["status"] }) {
  if (status === "done") {
    return (
      <span role="img" aria-label="Completat" className="flex size-6 items-center justify-center rounded-full bg-high-tint text-high-text">
        <Icon path={iconPath.check} size={14} strokeWidth={3} />
      </span>
    );
  }
  if (status === "active") {
    return (
      <span role="img" aria-label="În lucru" className="flex size-6 items-center justify-center rounded-full border-2 border-accent">
        <span className="size-2 animate-pulse rounded-full bg-accent" />
      </span>
    );
  }
  return <span role="img" aria-label="Urmează" className="size-6 rounded-full border-2 border-dashed border-bar" />;
}

/** A component that shows the collapsible business card above the chat on mobile. */
export function MobileBusinessCard({
  answers,
  fields,
  doneCount,
}: {
  answers: Answers;
  fields: CardField[];
  doneCount: number;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="px-4 pt-3 lg:hidden">
      <div className="overflow-hidden rounded-[20px] border border-border bg-page">
        <button
          type="button"
          aria-expanded={isOpen}
          onClick={() => setIsOpen(!isOpen)}
          className="flex min-h-15 w-full cursor-pointer items-center gap-3 px-3.5 py-2.5 text-start"
        >
          <span className="flex size-10 shrink-0 items-center justify-center rounded-[13px] bg-accent-soft text-sm font-extrabold text-accent-strong">
            {getInitials(answers.businessName) || "?"}
          </span>
          <span className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="text-sm font-bold">Cartea de vizită</span>
            <span className="text-xs text-muted">
              {doneCount} din {stepCount} completate
            </span>
          </span>
          <Icon
            path={iconPath.chevronDown}
            size={20}
            className={`text-subtle transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          />
        </button>
        {isOpen ? (
          <ul className="m-0 flex list-none flex-col px-3.5 pb-2.5">
            {fields.map((field) => (
              <li key={field.label} className="flex items-center gap-2.5 border-t border-ring-track py-2 text-[13px]">
                <span className="w-24 shrink-0 font-semibold text-muted">{field.label}</span>
                <span className={`min-w-0 flex-1 font-semibold wrap-break-word ${field.status === "done" ? "text-ink" : "text-accent-hover"}`}>
                  {field.value}
                </span>
                <span
                  className={`flex size-5 shrink-0 items-center justify-center rounded-full text-high-text ${field.status === "done" ? "bg-high-tint" : "bg-accent-soft"}`}
                >
                  {field.status === "done" ? <Icon path={iconPath.check} size={12} strokeWidth={3.2} /> : null}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
