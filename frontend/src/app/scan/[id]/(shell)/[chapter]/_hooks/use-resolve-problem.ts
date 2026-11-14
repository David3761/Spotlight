import { useCallback, useRef, useState } from "react";
import type { ToastContent } from "@/components/Toast";
import { resolveProblem } from "@/lib/api";
import type { Problem, Report } from "@/lib/types";
import { getOptimisticReport } from "./optimistic-report";

/** A failed attempt to mark a problem fixed, kept so it can be retried. */
interface ResolveFailure {
  /** The error the request failed with. */
  error: unknown;
  /** The problem that couldn't be marked fixed. */
  problem: Problem;
}

/** Marks problems as fixed: updates the report at once, confirms with the server, and rolls back on failure. */
export function useResolveProblem(scanId: string, report: Report, setReport: (report: Report) => void) {
  const [toast, setToast] = useState<ToastContent | null>(null);
  const [failure, setFailure] = useState<ResolveFailure | null>(null);
  const isPendingRef = useRef(false);

  /** Marks a problem fixed and shows the points toast, or restores the report and keeps the failure. */
  const resolve = async (problem: Problem) => {
    if (isPendingRef.current) {
      return;
    }
    isPendingRef.current = true;
    setFailure(null);
    const previous = report;
    setReport(getOptimisticReport(report, problem.check_id));
    try {
      const update = await resolveProblem(scanId, problem.check_id);
      setReport(update.report);
      setToast({
        title: `+${update.chapter_points_added} puncte`,
        detail: `${problem.chapter_name_ro} a urcat la ${update.chapter_score}`,
      });
    } catch (error) {
      setReport(previous);
      setFailure({ error, problem });
    } finally {
      isPendingRef.current = false;
    }
  };

  /** Tries the failed problem again. */
  const retry = () => {
    if (failure) {
      void resolve(failure.problem);
    }
  };

  /** Hides the toast. */
  const dismissToast = useCallback(() => setToast(null), []);

  return { toast, dismissToast, error: failure?.error ?? null, hasFailed: failure !== null, resolve, retry };
}
