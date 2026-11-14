"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, createConversation, getPlaceCandidates, getPlaceFromLink, startScan } from "@/lib/api";
import type { BusinessType, PlaceCandidate, Platform } from "@/lib/types";
import {
  emptyAnswers,
  getCandidatesPrompt,
  getMessages,
  getPhasePrompt,
  getPlatformsTurn,
  getScanInputs,
  getStepNumber,
  isSelfReportPhase,
  selfReportSteps,
  type Answers,
  type ChatTurn,
  type Option,
  type Phase,
} from "@/app/start/_hooks/onboarding-model";

/** The request a retry repeats. */
type RetryKind = "search" | "link" | "submit";

/** A failed request, with what to repeat when the owner retries. */
interface Failure {
  /** The error the request threw. */
  error: unknown;
  /** The request to repeat. */
  retry: RetryKind;
}

/** Returns a bubble written by the assistant. */
function getAssistantTurn(text: string): ChatTurn {
  return { role: "assistant", text, kind: "text" };
}

/** Returns a bubble written by the owner. */
function getUserTurn(text: string, kind: ChatTurn["kind"] = "text"): ChatTurn {
  return { role: "user", text, kind };
}

/** The scripted conversation's state and actions. */
export type Onboarding = ReturnType<typeof useOnboarding>;

/** Runs the scripted onboarding conversation: answers, chat, requests, errors and the final scan start. */
export function useOnboarding() {
  const router = useRouter();
  const [turns, setTurns] = useState<ChatTurn[]>(() => [getAssistantTurn(getPhasePrompt("name") ?? "")]);
  const [answers, setAnswers] = useState<Answers>(emptyAnswers);
  const [phase, setPhase] = useState<Phase>("name");
  const [candidates, setCandidates] = useState<PlaceCandidate[]>([]);
  const [failedLink, setFailedLink] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const lastLink = useRef("");
  const startedScanId = useRef<string | null>(null);

  /** Adds the owner's bubbles and the next question, stores the answers and moves to the next phase. */
  function advance(userTurns: ChatTurn[], nextPhase: Phase, patch: Partial<Answers>) {
    const prompt = getPhasePrompt(nextPhase);
    setTurns((current) => [...current, ...userTurns, ...(prompt ? [getAssistantTurn(prompt)] : [])]);
    setAnswers((current) => ({ ...current, ...patch }));
    setPhase(nextPhase);
  }

  /** Stores the business name and asks for the type. */
  function submitName(name: string) {
    advance([getUserTurn(name)], "type", { businessName: name });
  }

  /** Stores a picked type, or opens the text input for "Altceva". */
  function pickType(option: Option<BusinessType>) {
    if (option.value === "altceva") {
      setPhase("typeOther");
      return;
    }
    advance([getUserTurn(option.label)], "location", { businessType: option.value, typeLabel: option.label });
  }

  /** Stores the type the owner typed for "Altceva". */
  function submitOtherType(label: string) {
    advance([getUserTurn(label)], "location", { businessType: "altceva", typeLabel: label });
  }

  /** Stores the city and the neighbourhood and asks about the website. */
  function submitLocation(city: string, neighborhood: string) {
    advance([getUserTurn(`${city}, ${neighborhood}`)], "website", { city, neighborhood });
  }

  /** Stores "Nu" for the website, or opens the URL input for "Da". */
  function answerWebsite(hasWebsite: boolean) {
    if (hasWebsite) {
      setPhase("websiteUrl");
      return;
    }
    advance([getUserTurn("Nu")], "maps", { hasWebsite: false, websiteUrl: null });
  }

  /** Stores the website URL and asks for the Google Maps profile. */
  function submitWebsiteUrl(url: string) {
    advance([getUserTurn(`Da · ${url}`)], "maps", { hasWebsite: true, websiteUrl: url });
  }

  /** Looks up the business on Google and shows the candidates. */
  async function searchPlaces() {
    setIsPending(true);
    setFailure(null);
    try {
      const response = await getPlaceCandidates({
        business_name: answers.businessName,
        city: answers.city,
        neighborhood: answers.neighborhood,
      });
      if (response.candidates.length === 0) {
        setTurns((current) => [
          ...current,
          getAssistantTurn("Nu am găsit niciun loc care să se potrivească. Lipește linkul afacerii tale."),
        ]);
        setPhase("maps");
        return;
      }
      setCandidates(response.candidates);
      setTurns((current) => [...current, getAssistantTurn(getCandidatesPrompt(response.candidates.length))]);
      setPhase("candidates");
    } catch (error) {
      setFailure({ error, retry: "search" });
    } finally {
      setIsPending(false);
    }
  }

  /** Adds the owner's "search me" bubble and looks the business up. */
  function chooseSearch() {
    setTurns((current) => [...current, getUserTurn("Caută-mă pe Google")]);
    void searchPlaces();
  }

  /** Resolves a pasted Google Maps link, or shows the unreadable-link state. */
  async function resolveLink(url: string) {
    setIsPending(true);
    setFailure(null);
    try {
      const place = await getPlaceFromLink(url);
      advance([], "profileClaimed", { googleChoice: "place", place, mapsUrl: url });
    } catch (error) {
      if (error instanceof ApiError && error.code === "unreadable_link") {
        setFailedLink(url);
        setPhase("mapsError");
      } else {
        setFailure({ error, retry: "link" });
      }
    } finally {
      setIsPending(false);
    }
  }

  /** Adds the pasted link as the owner's bubble and resolves it. */
  function submitLink(url: string) {
    lastLink.current = url;
    setTurns((current) => [...current, getUserTurn(url, "link")]);
    void resolveLink(url);
  }

  /** Stores the candidate the owner picked. */
  function pickCandidate(candidate: PlaceCandidate) {
    advance([getUserTurn(candidate.name)], "profileClaimed", { googleChoice: "place", place: candidate, mapsUrl: null });
  }

  /** Returns to the link input, from the candidates or the unreadable-link state. */
  function pasteLinkInstead() {
    setPhase("maps");
  }

  /** Stores that the owner has no Google profile and skips the Google questions. */
  function chooseNoGoogleProfile() {
    advance([getUserTurn("Nu am profil Google")], "social", { googleChoice: "none", place: null, mapsUrl: null });
  }

  /** Stores that the owner adds the Google profile later and moves on to the Google questions. */
  function skipGoogleProfile() {
    advance([getUserTurn("Sar peste, îl adaug mai târziu", "skipped")], "profileClaimed", {
      googleChoice: "later",
      place: null,
      mapsUrl: null,
    });
  }

  /** Stores the answer to the current self-report question and moves to the next one. */
  function answerSelfReport(option: Option<string>) {
    if (!isSelfReportPhase(phase)) {
      return;
    }
    const step = selfReportSteps[phase];
    advance([getUserTurn(option.label)], step.next, { selfReport: { ...answers.selfReport, [step.field]: option.value } });
  }

  /** Stores the social links; an empty one counts as skipped. */
  function submitSocial(instagram: string, tiktok: string) {
    const links = [
      { name: "Instagram", url: instagram.trim() },
      { name: "TikTok", url: tiktok.trim() },
    ];
    const socialTurns = links.map((link) =>
      link.url ? getUserTurn(link.url) : getUserTurn(`${link.name} · Sar peste`, "skipped"),
    );
    advance(socialTurns, "socialPost", {
      hasAnsweredSocial: true,
      instagramUrl: links[0].url || null,
      tiktokUrl: links[1].url || null,
    });
  }

  /** Adds a platform to the answers, or removes it when it is already chosen. */
  function togglePlatform(platform: Platform) {
    setAnswers((current) => ({
      ...current,
      usesNoOtherPlatforms: false,
      platforms: current.platforms.includes(platform)
        ? current.platforms.filter((chosen) => chosen !== platform)
        : [...current.platforms, platform],
    }));
  }

  /** Switches "Nu folosesc altele" on or off; switching it on clears the chosen platforms. */
  function toggleNoOtherPlatforms() {
    setAnswers((current) => ({
      ...current,
      platforms: [],
      usesNoOtherPlatforms: !current.usesNoOtherPlatforms,
    }));
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
      await createConversation(scanId, {
        kind: "onboarding",
        chapter_id: null,
        title: "Configurarea afacerii",
        messages: getMessages([...turns, getPlatformsTurn(answers)], new Date()),
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
    if (failure.retry === "search") {
      void searchPlaces();
    } else if (failure.retry === "link") {
      void resolveLink(lastLink.current);
    } else {
      void submit();
    }
  }

  return {
    turns,
    answers,
    phase,
    stepNumber: getStepNumber(phase),
    candidates,
    failedLink,
    failure,
    isBusy: isPending || isSubmitting,
    submitName,
    pickType,
    submitOtherType,
    submitLocation,
    answerWebsite,
    submitWebsiteUrl,
    chooseSearch,
    submitLink,
    pickCandidate,
    pasteLinkInstead,
    chooseNoGoogleProfile,
    skipGoogleProfile,
    answerSelfReport,
    submitSocial,
    togglePlatform,
    toggleNoOtherPlatforms,
    submit,
    retry,
  };
}
