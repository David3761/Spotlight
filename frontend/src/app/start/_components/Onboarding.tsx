"use client";

import { useEffect, useRef } from "react";
import { AnswerForm, type AnswerField } from "@/app/start/_components/AnswerForm";
import { BusinessCard, MobileBusinessCard } from "@/app/start/_components/BusinessCard";
import { ChatBubble } from "@/app/start/_components/ChatBubble";
import { LinkError } from "@/app/start/_components/LinkError";
import { PlaceCandidates } from "@/app/start/_components/PlaceCandidates";
import { QuickReplies, ToggleReplies } from "@/app/start/_components/QuickReplies";
import {
  businessTypeOptions,
  getCardFields,
  getPlatformsCtaLabel,
  isSelfReportPhase,
  linkIcon,
  platformOptions,
  selfReportSteps,
  stepCount,
  stepNames,
  type Phase,
} from "@/app/start/_hooks/onboarding-model";
import { useOnboarding, type Onboarding as OnboardingState } from "@/app/start/_hooks/use-onboarding";
import { AppLogo } from "@/components/AppLogo";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { buttonVariant, chipVariant } from "@/components/button-styles";
import { ErrorState } from "@/components/ErrorState";

/** The yes and no chips of the website question. */
const websiteOptions = [
  { label: "Da", value: true },
  { label: "Nu", value: false },
];

/** The two ways to continue from the Google Maps question besides pasting a link. */
const mapsOptions = [
  { label: "Caută-mă pe Google", id: "search" },
  { label: "Nu am profil Google", id: "none" },
];

/** The inputs of the answer bar for each phase that takes typed text. */
const answerFields: Partial<Record<Phase, AnswerField[]>> = {
  name: [{ label: "Numele afacerii", placeholder: "Numele afacerii tale…", inputMode: "text" }],
  typeOther: [{ label: "Tipul afacerii", placeholder: "Ce fel de afacere ai?", inputMode: "text" }],
  location: [
    { label: "Orașul", placeholder: "Orașul…", inputMode: "text" },
    { label: "Cartierul", placeholder: "Cartierul…", inputMode: "text" },
  ],
  websiteUrl: [{ label: "Adresa site-ului", placeholder: "Adresa site-ului tău…", inputMode: "url" }],
  maps: [
    {
      label: "Linkul de pe Google Maps",
      placeholder: "Sau lipește aici linkul de pe Google Maps…",
      inputMode: "url",
      icon: linkIcon,
    },
  ],
  mapsError: [{ label: "Linkul de pe Google Maps", placeholder: "Lipește alt link…", inputMode: "url", icon: linkIcon }],
  social: [
    { label: "Linkul de Instagram", placeholder: "Instagram · instagram.com/…", inputMode: "url", isOptional: true },
    { label: "Linkul de TikTok", placeholder: "TikTok · tiktok.com/@…", inputMode: "url", isOptional: true },
  ],
};

/** A component that runs the onboarding: the scripted chat, its answer bar and the business card. */
export function Onboarding() {
  const onboarding = useOnboarding();
  const { answers, phase, stepNumber, turns, failure, isBusy } = onboarding;
  const fields = getCardFields(answers, stepNumber);
  const doneCount = stepNumber - 1;
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ block: "end" });
  }, [turns.length, phase, failure, isBusy]);

  return (
    <div className="flex h-dvh flex-col bg-surface text-ink lg:h-auto lg:min-h-screen lg:bg-page">
      <Header stepNumber={stepNumber} />
      <main className="mx-auto flex min-h-0 w-full max-w-350 flex-1 flex-col gap-8 lg:flex-none lg:flex-row lg:flex-wrap lg:items-start lg:px-10 lg:py-8">
        <section
          aria-label="Conversație"
          className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-surface lg:h-191 lg:flex-999 lg:basis-140 lg:rounded-[28px] lg:border lg:border-border lg:shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_rgba(15,23,42,0.05)]"
        >
          <div className="hidden items-center gap-3 border-b border-divider px-7 py-4.5 lg:flex">
            <AssistantAvatar className="size-10" />
            <div className="flex flex-col gap-0.5">
              <span className="text-[15px] font-bold">Asistentul tău</span>
              <span className="text-[13px] text-muted">Te ajut să apari în recomandările lui Gemini</span>
            </div>
          </div>
          <MobileBusinessCard answers={answers} fields={fields} doneCount={doneCount} />
          <div
            aria-live="polite"
            className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto p-4 lg:gap-3.5 lg:px-7 lg:py-6"
          >
            <div className="mt-auto flex flex-col gap-2.5 lg:gap-3.5">
              {turns.map((turn, index) => (
                <ChatBubble key={index} turn={turn} />
              ))}
              {isBusy && phase !== "mapsError" ? <TypingIndicator /> : null}
              <PhaseReplies onboarding={onboarding} />
              {failure ? <ErrorState error={failure.error} onRetry={onboarding.retry} /> : null}
              <div ref={chatEnd} />
            </div>
          </div>
          <PhaseFooter onboarding={onboarding} />
        </section>
        <BusinessCard answers={answers} fields={fields} doneCount={doneCount} />
      </main>
    </div>
  );
}

/** A component that shows the top bar: the product name, the step label with its progress and "later". */
function Header({ stepNumber }: { stepNumber: number }) {
  return (
    <header className="flex flex-col gap-2.5 border-b border-divider bg-surface px-3 pt-2.5 pb-3 lg:min-h-18 lg:flex-row lg:items-center lg:justify-between lg:gap-6 lg:border-border lg:px-10 lg:py-3">
      <div className="hidden lg:block">
        <AppLogo />
      </div>
      <div className="flex items-center justify-between lg:flex-col lg:gap-2">
        <span className="ps-2.5 text-sm font-bold lg:ps-0 lg:text-[13px] lg:font-semibold lg:text-subtle">
          <span className="lg:hidden">
            Pasul {stepNumber} din {stepCount}
          </span>
          <span className="hidden lg:inline">
            Pasul {stepNumber} din {stepCount} · {stepNames[stepNumber - 1]}
          </span>
        </span>
        <span className="pe-2.5 text-sm font-semibold text-subtle lg:hidden">Mai târziu</span>
        <div
          role="progressbar"
          aria-label="Progres configurare"
          aria-valuemin={0}
          aria-valuemax={stepCount}
          aria-valuenow={stepNumber - 1}
          className="hidden gap-1.5 lg:flex"
        >
          {stepNames.map((name, index) => (
            <span
              key={name}
              className={`h-1.5 w-11 rounded-[3px] ${index + 1 < stepNumber ? "bg-accent" : index + 1 === stepNumber ? "bg-accent-line" : "bg-border"}`}
            />
          ))}
        </div>
      </div>
      <div
        role="progressbar"
        aria-label="Progres configurare"
        aria-valuemin={0}
        aria-valuemax={stepCount}
        aria-valuenow={stepNumber - 1}
        className="grid grid-cols-7 gap-1 px-1.5 lg:hidden"
      >
        {stepNames.map((name, index) => (
          <span
            key={name}
            className={`h-1.25 rounded-[3px] ${index + 1 < stepNumber ? "bg-accent" : index + 1 === stepNumber ? "bg-accent-line" : "bg-border"}`}
          />
        ))}
      </div>
      <span className="hidden h-11 items-center rounded-full border border-border bg-surface px-4.5 text-sm font-semibold text-subtle lg:inline-flex">
        Continui mai târziu
      </span>
    </header>
  );
}

/** A component that shows the answers to pick from, inside the chat, for the current phase. */
function PhaseReplies({ onboarding }: { onboarding: OnboardingState }) {
  const { phase, answers, candidates, failedLink, isBusy } = onboarding;
  if (phase === "type") {
    return (
      <QuickReplies
        groupLabel="Tipul afacerii"
        options={businessTypeOptions}
        isDisabled={isBusy}
        onSelect={onboarding.pickType}
      />
    );
  }
  if (phase === "website") {
    return (
      <QuickReplies
        groupLabel="Ai un site web?"
        options={websiteOptions}
        isDisabled={isBusy}
        onSelect={(option) => onboarding.answerWebsite(option.value)}
      />
    );
  }
  if (phase === "maps") {
    return (
      <QuickReplies
        groupLabel="Google Maps"
        options={mapsOptions}
        isDisabled={isBusy}
        onSelect={(option) => (option.id === "search" ? onboarding.chooseSearch() : onboarding.chooseNoGoogleProfile())}
      />
    );
  }
  if (phase === "candidates") {
    return (
      <PlaceCandidates
        candidates={candidates}
        isDisabled={isBusy}
        onPick={onboarding.pickCandidate}
        onPasteLink={onboarding.pasteLinkInstead}
      />
    );
  }
  if (phase === "mapsError" && failedLink !== null) {
    return (
      <LinkError
        isDisabled={isBusy}
        onSearch={onboarding.chooseSearch}
        onPasteLink={onboarding.pasteLinkInstead}
        onSkip={onboarding.skipGoogleProfile}
      />
    );
  }
  if (isSelfReportPhase(phase)) {
    return (
      <QuickReplies
        groupLabel="Răspunsuri"
        options={selfReportSteps[phase].options}
        isDisabled={isBusy}
        onSelect={onboarding.answerSelfReport}
      />
    );
  }
  if (phase === "platforms") {
    return (
      <ToggleReplies
        groupLabel="Alte platforme"
        options={platformOptions}
        chosen={answers.platforms}
        isDisabled={isBusy}
        onToggle={onboarding.togglePlatform}
      />
    );
  }
  return null;
}

/** A component that shows the bar under the chat: the text inputs of the phase, or the final button. */
function PhaseFooter({ onboarding }: { onboarding: OnboardingState }) {
  const { phase, answers, isBusy } = onboarding;
  if (phase === "platforms") {
    return (
      <div className="flex flex-col gap-1.5 border-t border-divider px-4 pt-3 pb-7 lg:px-6 lg:pb-4">
        <button
          type="button"
          disabled={isBusy}
          onClick={onboarding.submit}
          className={`${buttonVariant.primary} h-13 cursor-pointer text-[15px] disabled:cursor-default disabled:opacity-60`}
        >
          {getPlatformsCtaLabel(answers.platforms.length)}
        </button>
        <button
          type="button"
          aria-pressed={answers.usesNoOtherPlatforms}
          disabled={isBusy}
          onClick={onboarding.toggleNoOtherPlatforms}
          className={`${answers.usesNoOtherPlatforms ? chipVariant.pressed : ""} h-11 cursor-pointer text-sm font-semibold text-subtle disabled:cursor-default disabled:opacity-60`}
        >
          Nu folosesc altele
        </button>
      </div>
    );
  }
  const fields = answerFields[phase];
  if (!fields) {
    return null;
  }
  return <AnswerForm key={phase} fields={fields} isDisabled={isBusy} onSubmit={(values) => submitAnswer(onboarding, values)} />;
}

/** Sends the typed values of the current phase to the matching action. */
function submitAnswer(onboarding: OnboardingState, values: string[]) {
  const [first, second] = values;
  switch (onboarding.phase) {
    case "name":
      onboarding.submitName(first);
      return;
    case "typeOther":
      onboarding.submitOtherType(first);
      return;
    case "location":
      onboarding.submitLocation(first, second);
      return;
    case "websiteUrl":
      onboarding.submitWebsiteUrl(first);
      return;
    case "maps":
    case "mapsError":
      onboarding.submitLink(first);
      return;
    case "social":
      onboarding.submitSocial(first, second);
      return;
    default:
      return;
  }
}
