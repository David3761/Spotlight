import { Icon, iconPath } from "@/components/Icon";

/** The props of {@link AssistantCard}. */
interface AssistantCardProps {
  /** When `true`, the conversation is being created and the card is disabled. */
  isPending: boolean;
  /** Called when the owner opens a new conversation with the assistant. */
  onOpen: () => void;
}

/** A component that invites the owner to tell the assistant what they fixed. */
export function AssistantCard({ isPending, onOpen }: AssistantCardProps) {
  return (
    <button
      type="button"
      onClick={onOpen}
      disabled={isPending}
      className="flex min-w-0 flex-[1_1_300px] flex-col items-stretch gap-3.5 rounded-[28px] border border-border bg-surface px-7 py-6.5 text-start text-ink disabled:opacity-60"
    >
      <span className="flex size-12 items-center justify-center rounded-full bg-accent-soft">
        <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
          <path d={iconPath.sparkle} className="fill-accent" />
        </svg>
      </span>
      <span className="text-lg font-extrabold">Ai rezolvat ceva?</span>
      <span className="text-sm leading-[1.55] text-subtle">
        Spune-i asistentului ce ai făcut și îl marchează ca rezolvat. Îl poți întreba și ce să faci mai departe.
      </span>
      <span className="mt-auto flex h-11 items-center gap-2 self-start rounded-full border border-accent-outline px-4.5 text-sm font-bold text-accent-strong">
        Deschide conversația
        <Icon path={iconPath.chevronRight} size={16} strokeWidth={2.2} />
      </span>
    </button>
  );
}
