import { useState } from "react";
import { useRouter } from "next/navigation";
import { createConversation } from "@/lib/api";

/** Creates an assistant conversation for the scan and opens it. */
export function useOpenAssistant(scanId: string) {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  /** Creates the conversation and navigates to it; stays pending until the navigation leaves the page. */
  const openAssistant = async () => {
    setIsPending(true);
    setError(null);
    try {
      const created = await createConversation(scanId, { kind: "assistant", chapter_id: null, title: null, messages: null });
      router.push(`/scan/${scanId}/conversatii/${created.cid}`);
    } catch (caught) {
      setError(caught);
      setIsPending(false);
    }
  };

  return { openAssistant, isPending, error };
}
