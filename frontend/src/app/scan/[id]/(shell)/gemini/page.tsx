"use client";

import { useLoadedScan } from "@/components/ScanShell";
import { Comparison } from "./_components/Comparison";
import { GeminiHeader } from "./_components/GeminiHeader";
import { PromptGroup } from "./_components/PromptGroup";
import { useGeminiRetest } from "./_hooks/use-gemini-retest";

/** A component that shows how visible the business is in Gemini, what Gemini answered and why it picks the competitors. */
export default function GeminiPage() {
  const { scanId, report, setReport } = useLoadedScan();
  const { isTesting, hasRetested, error, retest } = useGeminiRetest(scanId, setReport);
  const { gemini, comparison } = report;

  return (
    <div className="flex flex-col lg:gap-6 lg:px-12 lg:pt-8 lg:pb-14">
      <GeminiHeader
        scanId={scanId}
        gemini={gemini}
        isTesting={isTesting}
        hasRetested={hasRetested}
        error={error}
        onRetest={retest}
      />
      <div className="flex flex-col gap-3.5 px-4 pb-5 lg:gap-6 lg:p-0">
        <div className="flex flex-col gap-3.5 lg:flex-row lg:flex-wrap lg:items-stretch lg:gap-5">
          {gemini.groups.map((group) => (
            <PromptGroup key={group.id} group={group} />
          ))}
        </div>
        {comparison.rivals.length > 0 && <Comparison scanId={scanId} comparison={comparison} />}
      </div>
    </div>
  );
}
