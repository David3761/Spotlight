"use client";

import { motion } from "motion/react";
import { Icon, iconPath } from "@/components/Icon";
import type { StepId } from "@/lib/types";
import { steps, type StepTexts } from "./steps";

/** Where a step is: finished, the first unfinished one, or waiting. */
type StepState = "done" | "active" | "pending";

/** The state label, colour and icon of each step state. */
const stateLook: Record<StepState, { label: string; labelClass: string }> = {
  done: { label: "Gata", labelClass: "text-high-text" },
  active: { label: "Acum", labelClass: "text-accent-hover" },
  pending: { label: "Urmează", labelClass: "text-faint" },
};

/** A component that lists the five steps; the first unfinished one is active. */
export function StepList({ doneDetails }: { doneDetails: Partial<Record<StepId, string | null>> }) {
  const activeIndex = steps.findIndex((step) => !(step.id in doneDetails));

  return (
    <ol className="m-0 flex w-full list-none flex-col gap-0.5 rounded-3xl border border-border bg-surface p-2 lg:gap-2 lg:border-0 lg:bg-transparent lg:p-0">
      {steps.map((step, index) => {
        const state: StepState = step.id in doneDetails ? "done" : index === activeIndex ? "active" : "pending";
        return <StepRow key={step.id} step={step} state={state} doneDetail={doneDetails[step.id] ?? null} />;
      })}
    </ol>
  );
}

/** A component that shows one step with its marker, title, detail line and (on desktop) state label. */
function StepRow({ step, state, doneDetail }: { step: StepTexts; state: StepState; doneDetail: string | null }) {
  const detail = { done: doneDetail, active: step.active, pending: step.pending }[state];

  return (
    <li
      className={`flex items-center gap-3 rounded-2xl p-3 lg:gap-3.5 lg:rounded-[18px] lg:px-4 lg:py-3.5 ${
        state === "active" ? "bg-accent-wash" : ""
      }`}
    >
      {state === "done" && (
        <span className="flex size-7.5 flex-none items-center justify-center rounded-full bg-high text-white lg:size-8">
          <Icon path={iconPath.check} size={16} strokeWidth={3} />
        </span>
      )}
      {state === "active" && (
        <motion.span
          aria-hidden="true"
          className="size-7.5 flex-none rounded-full border-3 border-accent-outline border-t-accent lg:size-8"
          animate={{ rotate: 360 }}
          transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
        />
      )}
      {state === "pending" && (
        <span aria-hidden="true" className="size-7.5 flex-none rounded-full border-2 border-dashed border-bar lg:size-8" />
      )}
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className={`text-[15px] font-bold ${state === "pending" ? "text-muted" : "text-ink"}`}>{step.title}</span>
        <span className="text-xs text-muted lg:text-[13px]">{detail}</span>
      </span>
      <span className={`hidden text-[13px] font-bold lg:block ${stateLook[state].labelClass}`}>{stateLook[state].label}</span>
    </li>
  );
}
