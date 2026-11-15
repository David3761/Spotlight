"use client";

import { useEffect, useRef } from "react";
import { AnswerForm } from "@/app/start/_components/AnswerForm";
import { BusinessCard, MobileBusinessCard } from "@/app/start/_components/BusinessCard";
import { ChatBubble } from "@/app/start/_components/ChatBubble";
import { PlaceCandidates } from "@/app/start/_components/PlaceCandidates";
import { QuickReplies, ToggleReplies } from "@/app/start/_components/QuickReplies";
import {
  getCardFields,
  getDoneCount,
  getPlaceholder,
  getPlatformsCtaLabel,
  getQuickReplies,
  isAtLastStep,
  platformOptions,
  stepCount,
  stepNames,
  usesNoOtherPlatforms,
} from "@/app/start/_hooks/onboarding-model";
import { useOnboarding, type Onboarding as OnboardingState } from "@/app/start/_hooks/use-onboarding";
import { AppLogo } from "@/components/AppLogo";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { buttonVariant, chipVariant } from "@/components/button-styles";
import { ErrorState } from "@/components/ErrorState";

/** A component that runs the onboarding: the chat the assistant leads, its answer bar and the business card. */
export function Onboarding() {
  const onboarding = useOnboarding();
  const { answers, missing, stepNumber, messages, failure, isBusy } = onboarding;
  const fields = getCardFields(answers, missing);
  const doneCount = getDoneCount(missing);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ block: "end" });
  }, [messages.length, missing, failure, isBusy]);

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
              <span className="text-[13px] text-muted">Te ajut să apari în recomandările LLM-ului</span>
            </div>
          </div>
          <MobileBusinessCard answers={answers} fields={fields} doneCount={doneCount} />
          <div
            aria-live="polite"
            className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto p-4 lg:gap-3.5 lg:px-7 lg:py-6"
          >
            <div className="mt-auto flex flex-col gap-2.5 lg:gap-3.5">
              {messages.map((message, index) => (
                <ChatBubble key={index} message={message} />
              ))}
              {onboarding.isReplying ? <TypingIndicator /> : <Replies onboarding={onboarding} />}
              {failure ? <ErrorState error={failure.error} onRetry={onboarding.retry} /> : null}
              <div ref={chatEnd} />
            </div>
          </div>
          <Footer onboarding={onboarding} />
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

/** A component that shows, inside the chat, the answers to pick for the question being asked. */
function Replies({ onboarding }: { onboarding: OnboardingState }) {
  const { asks, answers, candidates, isBusy } = onboarding;
  if (isAtLastStep(asks)) {
    return (
      <ToggleReplies
        groupLabel="Alte platforme"
        options={platformOptions}
        chosen={answers.platforms ?? []}
        isDisabled={isBusy}
        onToggle={onboarding.togglePlatform}
      />
    );
  }
  const replies = getQuickReplies(asks).map((label) => ({ label }));
  return (
    <>
      {asks === "google_profile" && candidates.length > 0 ? (
        <PlaceCandidates candidates={candidates} isDisabled={isBusy} onPick={onboarding.pickCandidate} />
      ) : null}
      {replies.length > 0 ? (
        <QuickReplies
          groupLabel="Răspunsuri rapide"
          options={replies}
          isDisabled={isBusy}
          onSelect={(reply) => onboarding.send(reply.label)}
        />
      ) : null}
    </>
  );
}

/** A component that shows the bar under the chat: the text box, or the button that starts the analysis at the end. */
function Footer({ onboarding }: { onboarding: OnboardingState }) {
  const { asks, answers, messages, isBusy } = onboarding;
  if (isAtLastStep(asks)) {
    return (
      <div className="flex flex-col gap-1.5 border-t border-divider px-4 pt-3 pb-7 lg:px-6 lg:pb-4">
        <button
          type="button"
          disabled={isBusy}
          onClick={onboarding.submit}
          className={`${buttonVariant.primary} h-13 cursor-pointer text-[15px] disabled:cursor-default disabled:opacity-60`}
        >
          {getPlatformsCtaLabel(answers.platforms?.length ?? 0)}
        </button>
        <button
          type="button"
          aria-pressed={usesNoOtherPlatforms(answers)}
          disabled={isBusy}
          onClick={onboarding.toggleNoOtherPlatforms}
          className={`${usesNoOtherPlatforms(answers) ? chipVariant.pressed : ""} h-11 cursor-pointer text-sm font-semibold text-subtle disabled:cursor-default disabled:opacity-60`}
        >
          Nu folosesc altele
        </button>
      </div>
    );
  }
  return (
    <AnswerForm
      key={messages.length}
      fields={[{ label: "Răspunsul tău", placeholder: getPlaceholder(asks), inputMode: "text" }]}
      isDisabled={isBusy}
      onSubmit={(values) => onboarding.send(values[0])}
    />
  );
}
