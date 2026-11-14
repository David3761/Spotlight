import useSWR from "swr";
import { getConversations } from "@/lib/api";
import type { ConversationList } from "@/lib/types";

/** Loads a scan's conversations, newest first. */
export function useConversations(scanId: string) {
  const { data, error, isLoading, mutate } = useSWR<ConversationList>(`conversations:${scanId}`, () =>
    getConversations(scanId),
  );

  return { conversations: data?.conversations, error, isLoading, retry: () => mutate() };
}
