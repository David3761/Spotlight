import { useState } from "react";
import { useRouter } from "next/navigation";
import { createConversation, sendMessage } from "@/lib/api";

/** A conversation being started. */
interface Starting {
  /** The text sent as the first message; `null` for an empty conversation. */
  firstMessage: string | null;
}

/** A conversation that couldn't be started. */
interface StartFailure {
  /** The text that was to be sent as the first message. */
  firstMessage: string | null;
  /** The ID of the conversation if it was already created, so a retry doesn't create another. */
  cid: string | null;
  /** The error of the failed request. */
  error: unknown;
}

/** Starts conversations for a scan: creates one, sends the first message if any, then opens it. */
export function useStartConversation(scanId: string) {
  const router = useRouter();
  const [starting, setStarting] = useState<Starting | null>(null);
  const [failure, setFailure] = useState<StartFailure | null>(null);

  /** Creates a conversation (unless `existingCid` is given), sends `firstMessage` and opens the conversation. */
  const start = async (firstMessage: string | null, existingCid: string | null = null) => {
    if (starting) {
      return;
    }
    setStarting({ firstMessage });
    setFailure(null);
    let cid = existingCid;
    try {
      if (cid === null) {
        const created = await createConversation(scanId, { kind: "assistant", chapter_id: null, title: null, messages: null });
        cid = created.cid;
      }
      if (firstMessage !== null) {
        await sendMessage(cid, firstMessage);
      }
      router.push(`/scan/${scanId}/conversatii/${cid}`);
    } catch (error) {
      setFailure({ firstMessage, cid, error });
      setStarting(null);
    }
  };

  /** Starts the conversation that failed again. */
  const retry = () => {
    if (failure) {
      void start(failure.firstMessage, failure.cid);
    }
  };

  return { starting, failure, start, retry };
}
