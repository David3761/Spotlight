"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ErrorState, getErrorMessage } from "@/components/ErrorState";
import { Icon, iconPath } from "@/components/Icon";
import { useLoadedScan } from "@/components/ScanShell";
import { Toast } from "@/components/Toast";
import { buttonVariant } from "@/components/button-styles";
import type { Conversation } from "@/lib/types";
import { ChatComposer } from "../_components/ChatComposer";
import { ChatMessages } from "../_components/ChatMessages";
import { ChapterStrip, ChatPanel } from "../_components/ChatPanel";
import { getChapterTasks, getConfirmedItems, getPanelChapter } from "../_components/chat-data";
import { getConversationDayLabel, getTimeLabel } from "../_components/conversation-groups";
import { useChat } from "../_hooks/use-chat";

/** The path of the back arrow. */

/** The chat page: the conversation with the assistant and, on desktop, the chapter and score panel. */
export default function ChatPage() {
  const { cid } = useParams<{ cid: string }>();
  const { scanId, report } = useLoadedScan();
  const { conversation, error, isLoading, isSending, isAnswering, failure, toast, send, answer, dismissToast, retry } =
    useChat(cid);
  const [draft, setDraft] = useState("");
  const [overallAtOpen] = useState(report.overall);

  const isBusy = isSending || isAnswering;
  const listHref = `/scan/${scanId}/conversatii`;

  /** Sends a message and puts the text back in the input when it fails. */
  const submit = async (text: string) => {
    setDraft("");
    const isSent = await send(text);
    if (!isSent) {
      setDraft((current) => current || text);
    }
  };

  /** Repeats the request that failed. */
  const retryFailure = () => {
    if (failure?.kind === "send") {
      void submit(failure.text);
    } else if (failure?.kind === "answer") {
      void answer(failure.actionId, failure.optionId);
    }
  };

  const messages = conversation?.messages ?? [];
  const confirmedItems = getConfirmedItems(report, messages);
  const chapter = getPanelChapter(report, conversation?.chapter_id ?? null, confirmedItems);
  const tasks = chapter ? getChapterTasks(chapter, confirmedItems) : [];

  return (
    <div className="flex min-h-dvh flex-col lg:flex-row lg:flex-wrap lg:items-start lg:gap-6 lg:px-10 lg:py-8">
      <section
        aria-label="Conversație"
        className="relative flex h-dvh min-w-0 flex-1 flex-col bg-surface lg:h-224 lg:flex-[999_1_520px] lg:overflow-hidden lg:rounded-[28px] lg:border lg:border-border lg:shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_rgba(15,23,42,0.05)]"
      >
        <header className="flex items-center gap-1 border-b border-divider px-3 py-2 lg:gap-2 lg:px-5 lg:py-3.5">
          <Link
            href={listHref}
            aria-label="Înapoi la conversații"
            className="flex size-11 flex-none items-center justify-center rounded-full text-body"
          >
            <Icon path={iconPath.back} size={22} strokeWidth={2.2} />
          </Link>
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="truncate text-[15px] font-extrabold lg:text-base">{conversation?.title}</span>
            {conversation && (
              <span className="hidden truncate text-[13px] text-muted lg:block">{getSubtitle(conversation, report.chapters)}</span>
            )}
          </div>
        </header>

        {chapter && <ChapterStrip chapter={chapter} tasks={tasks} />}

        {isLoading && <div aria-busy="true" className="flex-1" />}
        {error && (
          <div className="p-4 lg:p-7">
            <ErrorState error={error} onRetry={retry} />
          </div>
        )}
        {conversation && (
          <>
            <ChatMessages
              messages={messages}
              isTyping={isBusy}
              isBusy={isBusy}
              onReply={submit}
              onOption={answer}
            />
            {failure && (
              <div role="alert" className="mx-3 mb-1 flex flex-wrap items-center gap-3 rounded-2xl bg-low-tint px-4 py-3 lg:mx-5">
                <p className="min-w-0 flex-1 text-sm font-medium text-low-text">{getErrorMessage(failure.error)}</p>
                <button type="button" onClick={retryFailure} className={`${buttonVariant.primary} h-10 px-4 text-sm`}>
                  Încearcă din nou
                </button>
              </div>
            )}
            <ChatComposer value={draft} isBusy={isBusy} onChange={setDraft} onSend={submit} />
          </>
        )}
      </section>

      <ChatPanel chapter={chapter} tasks={tasks} overall={report.overall} overallAtOpen={overallAtOpen} />
      <Toast toast={toast} onDismiss={dismissToast} />
    </div>
  );
}

/** Returns the line under the title: the day and time of the last message, then the chapter. */
function getSubtitle(conversation: Conversation, chapters: { id: string; name_ro: string }[]): string {
  const lastMessage = conversation.messages[conversation.messages.length - 1];
  const chapterName =
    conversation.kind === "onboarding" ? "Configurare" : chapters.find((chapter) => chapter.id === conversation.chapter_id)?.name_ro;
  const when = lastMessage
    ? `${getConversationDayLabel(new Date(lastMessage.created_at))}, ${getTimeLabel(lastMessage.created_at)}`
    : null;
  return [when, chapterName].filter(Boolean).join(" · ");
}
