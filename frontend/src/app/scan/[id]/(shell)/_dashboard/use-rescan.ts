import { useState } from "react";
import { useRouter } from "next/navigation";
import { rescan } from "@/lib/api";

/** Starts a new scan with the same inputs and opens its loading screen. */
export function useRescan(scanId: string) {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  /** Requests the rescan and navigates to the new scan; stays pending until the navigation leaves the page. */
  const startRescan = async () => {
    setIsPending(true);
    setError(null);
    try {
      const started = await rescan(scanId);
      router.push(`/scan/${started.scan_id}/loading`);
    } catch (caught) {
      setError(caught);
      setIsPending(false);
    }
  };

  return { startRescan, isPending, error };
}
