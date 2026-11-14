import { AssistantAvatar } from "@/app/start/_components/AssistantAvatar";

/** A component that shows the assistant is working on a request. */
export function TypingIndicator() {
  return (
    <div role="status" className="flex items-end gap-2 lg:gap-3">
      <AssistantAvatar className="size-7 lg:size-8" />
      <span className="flex items-center gap-1.5 rounded-[18px] rounded-es-[6px] bg-fill px-4 py-4 lg:rounded-[20px] lg:rounded-es-[6px]">
        <span className="size-2 animate-pulse rounded-full bg-faint" />
        <span className="size-2 animate-pulse rounded-full bg-faint [animation-delay:200ms]" />
        <span className="size-2 animate-pulse rounded-full bg-faint [animation-delay:400ms]" />
        <span className="sr-only">Se încarcă</span>
      </span>
    </div>
  );
}
