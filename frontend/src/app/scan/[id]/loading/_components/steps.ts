import type { StepId } from "@/lib/types";

/** The texts of one analysis step. */
export interface StepTexts {
  /** The step's ID. */
  id: StepId;
  /** The step's title. */
  title: string;
  /** The line shown while the step runs. */
  active: string;
  /** The line shown before the step starts. */
  pending: string;
}

/** The five analysis steps in display order. */
export const steps: StepTexts[] = [
  { id: "google", title: "Google", active: "Căutăm Profilul tău Google…", pending: "Profilul tău Google" },
  { id: "recenzii", title: "Recenzii", active: "Citim recenziile…", pending: "Ce spun clienții despre tine" },
  { id: "website", title: "Website", active: "Citim site-ul…", pending: "Site-ul tău" },
  { id: "retele", title: "Rețele sociale", active: "Verificăm Instagram…", pending: "Instagram" },
  {
    id: "gemini",
    title: "LLM",
    active: "Îi punem LLM-ului 12 întrebări…",
    pending: "12 întrebări ca ale clienților tăi",
  },
];

/** Returns the progress bar's fill: each finished step counts fully and the running one half. */
export function getProgressPercent(doneCount: number): number {
  const runningHalf = doneCount < steps.length ? 0.5 : 0;
  return Math.min(100, Math.round(((doneCount + runningHalf) / steps.length) * 100));
}
