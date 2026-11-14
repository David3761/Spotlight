"use client";

import { useState } from "react";
import { runGeminiTest } from "@/lib/api";
import type { Report } from "@/lib/types";

/** Runs the live Gemini test again and tracks whether it is running, failed or just finished. */
export function useGeminiRetest(scanId: string, setReport: (report: Report) => void) {
  const [isTesting, setIsTesting] = useState(false);
  const [hasRetested, setHasRetested] = useState(false);
  const [error, setError] = useState<unknown>(null);

  /** Starts the test, replaces the report on success and keeps the error on failure. */
  const retest = async () => {
    if (isTesting) {
      return;
    }
    setIsTesting(true);
    setError(null);
    try {
      const newReport = await runGeminiTest(scanId);
      setReport(newReport);
      setHasRetested(true);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsTesting(false);
    }
  };

  return { isTesting, hasRetested, error, retest };
}
