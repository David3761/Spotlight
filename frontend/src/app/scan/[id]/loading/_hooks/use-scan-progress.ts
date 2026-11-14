import { useEffect, useState } from "react";
import { subscribeToScanEvents } from "@/lib/api";
import type { ScanEvent, StepId } from "@/lib/types";

/** Where the analysis is, as far as the stream has told us. */
export type ScanOutcome = "running" | "complete" | "failed" | "disconnected";

/** What the progress stream has reported so far. */
interface ScanProgress {
  /** The finished steps with their detail line; a step is done when it has an entry. */
  doneDetails: Partial<Record<StepId, string | null>>;
  /** Where the analysis is. */
  outcome: ScanOutcome;
  /** The failure message, set when the outcome is `failed`. */
  failureMessage: string | null;
}

/** The progress before any event arrived. */
const initialProgress: ScanProgress = { doneDetails: {}, outcome: "running", failureMessage: null };

/** Returns the progress after one stream event. */
function getProgressAfter(progress: ScanProgress, event: ScanEvent): ScanProgress {
  switch (event.type) {
    case "step":
      if (event.status !== "done") {
        return progress;
      }
      return { ...progress, doneDetails: { ...progress.doneDetails, [event.step]: event.detail_ro } };
    case "complete":
      return { ...progress, outcome: "complete" };
    case "failed":
      return { ...progress, outcome: "failed", failureMessage: event.message_ro };
  }
}

/** Follows a scan's progress stream; `retry` resubscribes after the connection was lost. */
export function useScanProgress(scanId: string) {
  const [progress, setProgress] = useState(initialProgress);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const close = subscribeToScanEvents(
      scanId,
      (event) => {
        setProgress((current) => getProgressAfter(current, event));
        if (event.type !== "step") {
          close();
        }
      },
      () => {
        setProgress((current) => (current.outcome === "running" ? { ...current, outcome: "disconnected" } : current));
        close();
      },
    );
    return close;
  }, [scanId, attempt]);

  /** Clears the progress and subscribes again. */
  const retry = () => {
    setProgress(initialProgress);
    setAttempt(attempt + 1);
  };

  return { ...progress, retry };
}
