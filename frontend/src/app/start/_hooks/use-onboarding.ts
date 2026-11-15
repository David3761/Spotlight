"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createConversation, sendOnboardingMessage, startScan } from "@/lib/api";
import type { OnboardingAnswers, OnboardingField, OnboardingMessage, PlaceCandidate, Platform } from "@/lib/types";
import {
  allFields,
  emptyAnswers,
  getMessages,
  getPlatformsMessage,
  getScanInputs,
  getStepNumber,
  greeting,
} from "@/app/start/_hooks/onboarding-model";

/** A failed request, with what to repeat when the owner retries. */
interface Failure {
  /** The error the request threw. */
  error: unknown;
  /** The request to repeat: the assistant's reply to the owner's last message, or the scan start. */
  retry: "reply" | "submit";
}

/** The onboarding conversation's state and actions. */
export type Onboarding = ReturnType<typeof useOnboarding>;

/** Runs the onboarding conversation the assistant leads: chat, answers, requests, errors and the final scan start. */
export function useOnboarding() {
  const router = useRouter();
  const [messages, setMessages] = useState<OnboardingMessage[]>([{ role: "assistant", text: greeting }]);
  const [answers, setAnswers] = useState<OnboardingAnswers>(emptyAnswers);
  const [missing, setMissing] = useState<OnboardingField[]>(allFields);
  const [candidates, setCandidates] = useState<PlaceCandidate[]>([]);
  const [isPending, setIsPending] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const startedScanId = useRef<string | null>(null);

  /** Adds the owner's message, with any answers it sets directly, and asks the assistant for the next step. */
  function send(text: string, sentAnswers: OnboardingAnswers = answers) {
    const chat: OnboardingMessage[] = [...messages, { role: "user", text }];
    setMessages(chat);
    setAnswers(sentAnswers);
    void requestReply(chat, sentAnswers);
  }

  /** Sends the chat to the assistant and shows its reply with the answers it collected. */
  async function requestReply(chat: OnboardingMessage[], sentAnswers: OnboardingAnswers) {
    setIsPending(true);
    setFailure(null);
    try {
      const turn = await sendOnboardingMessage({ messages: chat, answers: sentAnswers });
      setMessages([...chat, { role: "assistant", text: turn.reply_ro }]);
      setAnswers(turn.answers);
      setMissing(turn.missing);
      setCandidates(turn.candidates);
    } catch (error) {
      setFailure({ error, retry: "reply" });
    } finally {
      setIsPending(false);
    }
  }

  /** Picks a Google place from the cards and tells the assistant. */
  function pickCandidate(candidate: PlaceCandidate) {
    send(`Asta sunt eu: ${candidate.name}`, { ...answers, google_choice: "place", place: candidate, maps_url: null });
  }

  /** Adds a platform to the answers, or removes it when it is already chosen. */
  function togglePlatform(platform: Platform) {
    setAnswers((current) => {
      const chosen = current.platforms ?? [];
      const next = chosen.includes(platform) ? chosen.filter((item) => item !== platform) : [...chosen, platform];
      return { ...current, platforms: next.length > 0 ? next : null };
    });
  }

  /** Switches "Nu folosesc altele" on or off; switching it on clears the chosen platforms. */
  function toggleNoOtherPlatforms() {
    setAnswers((current) => ({ ...current, platforms: current.platforms?.length === 0 ? null : [] }));
  }

  /** Starts the scan, saves the transcript and opens the loading page; a retry reuses a scan already started. */
  async function submit() {
    setIsSubmitting(true);
    setFailure(null);
    try {
      let scanId = startedScanId.current;
      if (scanId === null) {
        const started = await startScan(getScanInputs(answers));
        scanId = started.scan_id;
        startedScanId.current = scanId;
      }
      const transcript = missing.includes("platforms") ? [...messages, getPlatformsMessage(answers)] : messages;
      await createConversation(scanId, {
        kind: "onboarding",
        chapter_id: null,
        title: "Configurarea afacerii",
        messages: getMessages(transcript, new Date()),
      });
      router.push(`/scan/${scanId}/loading`);
    } catch (error) {
      setFailure({ error, retry: "submit" });
      setIsSubmitting(false);
    }
  }

  /** Repeats the request that failed. */
  function retry() {
    if (failure === null) {
      return;
    }
    if (failure.retry === "reply") {
      void requestReply(messages, answers);
    } else {
      void submit();
    }
  }

  return {
    messages,
    answers,
    missing,
    asks: missing[0] ?? null,
    stepNumber: getStepNumber(missing),
    candidates,
    failure,
    isReplying: isPending,
    isBusy: isPending || isSubmitting,
    send,
    pickCandidate,
    togglePlatform,
    toggleNoOtherPlatforms,
    submit,
    retry,
  };
}
