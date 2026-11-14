import useSWR from "swr";
import { getDevExport } from "@/lib/api";
import type { DevExport } from "@/lib/types";

/** Loads the developer export of a scan once, without reloading it on focus. */
export function useDevExport(scanId: string) {
  const { data, error, isLoading, mutate } = useSWR<DevExport>(`dev-export:${scanId}`, () => getDevExport(scanId), {
    revalidateOnFocus: false,
  });
  return { devExport: data, error, isLoading, retry: () => mutate() };
}
