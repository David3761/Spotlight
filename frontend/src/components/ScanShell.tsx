"use client";

import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { ErrorState } from "@/components/ErrorState";
import { ApiError } from "@/lib/api";
import { Sidebar, type SidebarSection } from "@/components/Sidebar";
import { TabBar, type Tab } from "@/components/TabBar";
import { useScan } from "@/hooks/use-scan";
import type { ChapterId, Report } from "@/lib/types";

/** The loaded scan every page inside the shell reads. */
interface LoadedScan {
  /** The scan's ID. */
  scanId: string;
  /** The scan's report. */
  report: Report;
  /** Replaces the report in the shared cache, e.g. after a problem is marked fixed. */
  setReport: (report: Report) => void;
}

/** The context that carries the loaded scan to the pages. */
const LoadedScanContext = createContext<LoadedScan | null>(null);

/** Returns the loaded scan; only valid inside {@link ScanShell}. */
export function useLoadedScan(): LoadedScan {
  const loaded = useContext(LoadedScanContext);
  if (!loaded) {
    throw new Error("useLoadedScan must be used inside ScanShell");
  }
  return loaded;
}

/** The chapter IDs, to tell chapter routes apart from the other routes. */
const chapterIds: ChapterId[] = ["profil", "recenzii", "continut", "site", "info", "mentiuni", "social", "cunoaste"];

/** Returns the route segment after `/scan/{id}/`, or `null` on the dashboard. */
function getSection(pathname: string, scanId: string): string | null {
  return pathname.slice(`/scan/${scanId}`.length).split("/")[1] || null;
}

/** Returns the sidebar entry of a route section. */
function getSidebarSection(section: string | null): SidebarSection {
  if (section === null) {
    return "panou";
  }
  if (section === "gemini" || section === "conversatii") {
    return section;
  }
  return chapterIds.find((id) => id === section) ?? null;
}

/** Returns the tab of a route section. */
function getTab(section: string | null): Tab {
  if (section === null) {
    return "acasa";
  }
  if (section === "gemini") {
    return "gemini";
  }
  if (section === "conversatii") {
    return "asistent";
  }
  return chapterIds.some((id) => id === section) ? "capitole" : null;
}

/** A component that loads the scan and frames every scan page with the sidebar (desktop) or tab bar (mobile). */
export function ScanShell({ children }: { children: ReactNode }) {
  const { id: scanId } = useParams<{ id: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const { envelope, report, error, isLoading, retry, setReport } = useScan(scanId);

  useEffect(() => {
    if (envelope?.status === "running") {
      router.replace(`/scan/${scanId}/loading`);
    }
  }, [envelope?.status, router, scanId]);

  if (error) {
    return (
      <div className="mx-auto w-full max-w-xl p-6">
        <ErrorState error={error} onRetry={retry} />
      </div>
    );
  }
  if (envelope?.status === "failed") {
    return (
      <div className="mx-auto w-full max-w-xl p-6">
        <ErrorState error={new ApiError("scan_failed", null, envelope.error_ro)} onRetry={() => router.push("/start")} />
      </div>
    );
  }
  if (isLoading || !report) {
    return <div aria-busy="true" className="min-h-screen bg-page" />;
  }

  const section = getSection(pathname, scanId);
  const isChatOpen = section === "conversatii" && pathname.split("/").length > 4;

  return (
    <LoadedScanContext.Provider value={{ scanId, report, setReport }}>
      <div className="flex min-h-screen bg-page text-ink">
        <aside className="sticky top-0 hidden h-screen w-70 shrink-0 overflow-y-auto border-e border-border bg-surface lg:block">
          <Sidebar report={report} active={getSidebarSection(section)} />
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="min-w-0 flex-1">{children}</main>
          {!isChatOpen && (
            <div className="sticky bottom-0 lg:hidden">
              <TabBar scanId={scanId} chapterHref={`/scan/${scanId}/${report.start_here ?? "profil"}`} active={getTab(section)} />
            </div>
          )}
        </div>
      </div>
    </LoadedScanContext.Provider>
  );
}
