import Link from "next/link";
import { Icon, chapterIconPath, iconPath } from "@/components/Icon";
import type { ConversationSummary } from "@/lib/types";
import { getTimeLabel, type DayGroup } from "./conversation-groups";

/** Returns the icon path of a conversation: its chapter's icon, the store for onboarding, else the chat bubble. */
function getConversationIcon(conversation: ConversationSummary): string {
  if (conversation.kind === "onboarding") {
    return iconPath.store;
  }
  return conversation.chapter_id ? chapterIconPath[conversation.chapter_id] : iconPath.chat;
}

/** A component that lists conversations under their day headings. */
export function ConversationList({ scanId, groups }: { scanId: string; groups: DayGroup[] }) {
  return (
    <div className="flex flex-col gap-3.5 lg:gap-4.5">
      {groups.map((group) => (
        <section key={group.label} className="flex flex-col gap-2 lg:gap-2.5">
          <h2 className="mx-1.5 text-xs font-bold tracking-[0.08em] text-muted uppercase lg:text-[13px]">{group.label}</h2>
          <div className="overflow-hidden rounded-[22px] border border-border bg-surface lg:rounded-3xl">
            {group.conversations.map((conversation) => (
              <ConversationRow key={conversation.cid} scanId={scanId} conversation={conversation} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

/** A component that links to one conversation with its icon, title, preview, chapter, solved count and time. */
function ConversationRow({ scanId, conversation }: { scanId: string; conversation: ConversationSummary }) {
  const time = getTimeLabel(conversation.updated_at);
  const hasSolved = conversation.solved_count > 0;

  return (
    <Link
      href={`/scan/${scanId}/conversatii/${conversation.cid}`}
      className="flex items-start gap-3 border-t border-fill p-3.5 text-ink first:border-t-0 lg:items-center lg:gap-4 lg:px-5 lg:py-4.5"
    >
      <span className="flex size-10 flex-none items-center justify-center rounded-[13px] bg-fill text-accent lg:size-11 lg:rounded-[14px]">
        <Icon path={getConversationIcon(conversation)} size={20} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1 lg:gap-1.25">
        <span className="flex justify-between gap-2">
          <span className="truncate text-[15px] font-bold lg:text-base">{conversation.title}</span>
          <span className="flex-none text-xs font-semibold text-muted lg:hidden">{time}</span>
        </span>
        <span className="truncate text-[13px] text-subtle lg:text-sm">{conversation.preview}</span>
        <span className={`${hasSolved ? "flex" : "hidden lg:flex"} flex-wrap gap-1.5 lg:mt-0.5`}>
          {conversation.chapter_name_ro && (
            <span className="hidden h-6 items-center rounded-full bg-fill px-2.5 text-xs font-bold text-body lg:flex">
              {conversation.chapter_name_ro}
            </span>
          )}
          {hasSolved && (
            <span className="flex h-5.5 items-center gap-1 rounded-full bg-high-tint ps-1.25 pe-2 text-[11px] font-bold text-high-text lg:h-6 lg:gap-1.25 lg:ps-1.5 lg:pe-2.5 lg:text-xs">
              <Icon path={iconPath.check} size={12} strokeWidth={3} />
              {conversation.solved_count} rezolvate
            </span>
          )}
        </span>
      </span>
      <span className="hidden flex-col items-end gap-2.5 lg:flex">
        <span className="text-[13px] font-semibold text-muted">{time}</span>
        <Icon path={iconPath.chevronRight} size={18} strokeWidth={2.2} className="text-faint" />
      </span>
    </Link>
  );
}
