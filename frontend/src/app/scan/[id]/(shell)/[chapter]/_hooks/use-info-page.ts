import useSWR from "swr";
import { getInfoPage } from "@/lib/api";
import type { InfoPage } from "@/lib/types";

/** Loads the generated info page of a scan once; the page is written by a model, so focus never reloads it. */
export function useInfoPage(scanId: string) {
  const { data, error, isLoading, mutate } = useSWR<InfoPage>(`info-page:${scanId}`, () => getInfoPage(scanId), {
    revalidateOnFocus: false,
  });
  return { infoPage: data, error, isLoading, retry: () => mutate() };
}
