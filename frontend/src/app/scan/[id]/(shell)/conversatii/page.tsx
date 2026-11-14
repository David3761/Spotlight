"use client";

import { useState } from "react";
import { ErrorState } from "@/components/ErrorState";
import { Icon } from "@/components/Icon";
import { useLoadedScan } from "@/components/ScanShell";
import { AssistantIdeas } from "./_components/AssistantIdeas";
import { ConversationList } from "./_components/ConversationList";
import { getDayGroups, getMatchesSearch } from "./_components/conversation-groups";
import { useConversations } from "./_hooks/use-conversations";
import { useStartConversation } from "./_hooks/use-start-conversation";

/** The path of the plus icon of the new-conversation button. */
const plusPath = "M12 5v14M5 12h14";

/** The path of the magnifier icon of the search field. */
const searchPath = "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4";

/** The conversation list page: search, conversations by day, a button for a new one and ideas to ask. */
export default function ConversationsPage() {
  const { scanId } = useLoadedScan();
  const { conversations, error, isLoading, retry } = useConversations(scanId);
  const { starting, failure, start, retry: retryStart } = useStartConversation(scanId);
  const [search, setSearch] = useState("");

  const matching = conversations?.filter((conversation) => getMatchesSearch(conversation, search));
  const groups = matching ? getDayGroups(matching, new Date()) : [];

  return (
    <div className="flex flex-col gap-3 pb-6 lg:gap-6 lg:px-12 lg:pt-10 lg:pb-14">
      <div className="flex flex-wrap items-center justify-between gap-4 ps-5 pe-4 pt-4.5 lg:items-end lg:p-0">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[26px] font-extrabold tracking-[-0.02em] lg:text-[32px]">Conversații</h1>
          <span className="hidden text-[15px] text-subtle lg:block">
            Tot ce ai vorbit cu asistentul. Poți continua oricând de unde ai rămas.
          </span>
        </div>
        <button
          type="button"
          disabled={starting !== null}
          onClick={() => start(null)}
          className="flex size-11 items-center justify-center gap-2 rounded-full bg-accent text-[15px] font-bold text-white hover:bg-accent-hover disabled:opacity-60 lg:h-12 lg:w-auto lg:px-5.5"
        >
          <Icon path={plusPath} size={20} strokeWidth={2.4} />
          <span className="sr-only lg:not-sr-only">Conversație nouă</span>
        </button>
      </div>

      {failure && (
        <div className="px-4 lg:px-0">
          <ErrorState error={failure.error} onRetry={retryStart} />
        </div>
      )}

      <div className="flex flex-wrap items-start gap-6 px-4 lg:px-0">
        <div className="flex min-w-0 flex-[999_1_520px] flex-col gap-3 lg:gap-4.5">
          <div className="flex h-11.5 items-center gap-2.5 rounded-full border border-border bg-surface px-4 text-muted lg:h-13 lg:px-4.5">
            <Icon path={searchPath} size={18} />
            <label htmlFor="searchChats" className="sr-only">
              Caută în conversații
            </label>
            <input
              id="searchChats"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Caută în conversații…"
              className="min-w-0 flex-1 bg-transparent text-[15px] text-ink outline-none"
            />
          </div>

          {error && <ErrorState error={error} onRetry={retry} />}
          {isLoading && <ConversationsSkeleton />}
          {matching && matching.length === 0 && (
            <p className="rounded-3xl border border-border bg-surface p-6 text-[15px] font-medium text-subtle">
              {conversations?.length === 0 ? "Nu ai nicio conversație încă." : "Nicio conversație găsită."}
            </p>
          )}
          {matching && matching.length > 0 && <ConversationList scanId={scanId} groups={groups} />}
        </div>
        <AssistantIdeas isDisabled={starting !== null} onPick={start} />
      </div>
    </div>
  );
}

/** A component that holds the place of the conversation list while it loads. */
function ConversationsSkeleton() {
  return (
    <div aria-busy="true" className="flex flex-col gap-2.5">
      <div className="h-4 w-16 rounded-full bg-fill" />
      <div className="h-60 rounded-3xl border border-border bg-surface" />
    </div>
  );
}
