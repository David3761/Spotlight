"use client";

import { ErrorState } from "@/components/ErrorState";
import { useLoadedScan } from "@/components/ScanShell";
import { AssistantCard } from "./AssistantCard";
import { ChapterGrid } from "./ChapterGrid";
import { DashboardHeader } from "./DashboardHeader";
import { GeminiCard } from "./GeminiCard";
import { NextSteps } from "./NextSteps";
import { OverallCard } from "./OverallCard";
import { useRescan } from "./use-rescan";
import { useStartConversation } from "@/hooks/use-start-conversation";

/** A component that shows the scan's dashboard: overall score, Gemini test, next steps and chapters. */
export function Dashboard() {
  const { scanId, report } = useLoadedScan();
  const rescan = useRescan(scanId);
  const assistant = useStartConversation(scanId);

  return (
    <div className="flex flex-col lg:gap-7 lg:px-12 lg:pt-10 lg:pb-14">
      <DashboardHeader
        business={report.business}
        checkedAt={report.checked_at}
        isRescanning={rescan.isPending}
        onRescan={rescan.startRescan}
      />
      <div className="flex flex-col gap-4 px-4 pt-2 pb-6 lg:gap-7 lg:p-0">
        {rescan.error !== null && <ErrorState error={rescan.error} onRetry={rescan.startRescan} />}
        <div className="flex flex-col gap-4 lg:flex-row lg:flex-wrap lg:gap-6">
          <OverallCard report={report} />
          <GeminiCard scanId={scanId} gemini={report.gemini} />
        </div>
        <div className="hidden items-stretch gap-6 lg:flex lg:flex-wrap">
          <NextSteps scanId={scanId} problems={report.next_steps} />
          <AssistantCard isPending={assistant.starting !== null} onOpen={() => assistant.start(null)} />
        </div>
        {assistant.failure && <ErrorState error={assistant.failure.error} onRetry={assistant.retry} />}
        <ChapterGrid scanId={scanId} chapters={report.chapters} />
      </div>
    </div>
  );
}
