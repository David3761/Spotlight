import useSWR from "swr";
import { getScan } from "@/lib/api";
import type { Report, ScanEnvelope } from "@/lib/types";

/** Returns the SWR cache key of a scan. */
export function getScanKey(scanId: string): string {
  return `scan:${scanId}`;
}

/** Loads a scan and keeps it in the shared cache, so every component reads the same report. */
export function useScan(scanId: string) {
  const { data, error, isLoading, mutate } = useSWR<ScanEnvelope>(getScanKey(scanId), () => getScan(scanId));

  /** Replaces the cached report without refetching. */
  const setReport = (report: Report) =>
    mutate((current) => (current ? { ...current, report } : current), { revalidate: false });

  return { envelope: data, report: data?.report ?? null, error, isLoading, retry: () => mutate(), setReport };
}
