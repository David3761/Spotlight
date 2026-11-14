import { useCallback, useState } from "react";
import useSWR from "swr";
import { useLoadedScan } from "@/components/ScanShell";
import type { ToastContent } from "@/components/Toast";
import { answerAction, getConversation, sendMessage } from "@/lib/api";
import type { Conversation, Message, ProposedAction } from "@/lib/types";

/** A request in the chat that failed. */
export type ChatFailure =
  | {
      /** The failed request sent a message. */
      kind: "send";
      /** The text that wasn't sent. */
      text: string;
      /** The error of the request. */
      error: unknown;
    }
  | {
      /** The failed request answered a proposed action. */
      kind: "answer";
      /** The action that wasn't answered. */
      actionId: string;
      /** The option that was picked. */
      optionId: string;
      /** The error of the request. */
      error: unknown;
    };

/** Loads a conversation and sends messages and action answers, keeping the cached conversation and the scan's report current. */
export function useChat(cid: string) {
  const { setReport } = useLoadedScan();
  const { data, error, isLoading, mutate } = useSWR<Conversation>(`conversation:${cid}`, () => getConversation(cid), {
    revalidateOnFocus: false,
  });
  const [isSending, setIsSending] = useState(false);
  const [isAnswering, setIsAnswering] = useState(false);
  const [failure, setFailure] = useState<ChatFailure | null>(null);
  const [toast, setToast] = useState<ToastContent | null>(null);

  /** Adds a message at the end of the cached conversation. */
  const appendMessage = (message: Message) => {
    mutate((current) => (current ? { ...current, messages: [...current.messages, message] } : current), {
      revalidate: false,
    });
  };

  /** Removes a message from the cached conversation. */
  const removeMessage = (messageId: string) => {
    mutate((current) => (current ? { ...current, messages: current.messages.filter((message) => message.id !== messageId) } : current), {
      revalidate: false,
    });
  };

  /** Replaces a proposed action in the cached conversation. */
  const replaceAction = (action: ProposedAction) => {
    mutate(
      (current) =>
        current
          ? {
              ...current,
              messages: current.messages.map((message) =>
                message.action?.action_id === action.action_id ? { ...message, action } : message,
              ),
            }
          : current,
      { revalidate: false },
    );
  };

  /** Sends the owner's message, showing it at once, and adds the reply; returns whether it worked. */
  const send = async (text: string): Promise<boolean> => {
    if (isSending || isAnswering) {
      return false;
    }
    setIsSending(true);
    setFailure(null);
    const userMessage: Message = {
      id: `local-${Date.now()}`,
      role: "user",
      text,
      created_at: new Date().toISOString(),
      action: null,
      chips: [],
    };
    appendMessage(userMessage);
    try {
      const { reply } = await sendMessage(cid, text);
      appendMessage(reply);
      return true;
    } catch (sendError) {
      removeMessage(userMessage.id);
      setFailure({ kind: "send", text, error: sendError });
      return false;
    } finally {
      setIsSending(false);
    }
  };

  /** Sends the owner's choice for a proposed action and applies the new scores and follow-up. */
  const answer = async (actionId: string, optionId: string) => {
    if (isSending || isAnswering) {
      return;
    }
    setIsAnswering(true);
    setFailure(null);
    try {
      const result = await answerAction(cid, actionId, optionId);
      replaceAction(result.action);
      if (result.score) {
        setReport(result.score.report);
        if (result.action.status === "confirmed") {
          setToast({ title: `+${result.score.chapter_points_added} puncte` });
        }
      }
      if (result.followup) {
        appendMessage(result.followup);
      }
    } catch (answerError) {
      setFailure({ kind: "answer", actionId, optionId, error: answerError });
    } finally {
      setIsAnswering(false);
    }
  };

  /** Hides the points toast. */
  const dismissToast = useCallback(() => setToast(null), []);

  return { conversation: data, error, isLoading, isSending, isAnswering, failure, toast, send, answer, dismissToast, retry: () => mutate() };
}
