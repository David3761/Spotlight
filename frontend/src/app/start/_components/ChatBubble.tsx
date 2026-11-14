import { linkIcon, type ChatTurn } from "@/app/start/_hooks/onboarding-model";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { AssistantBubble } from "@/components/chat/AssistantBubble";
import { Icon } from "@/components/Icon";

/** A component that shows one bubble of the conversation: the assistant's with its avatar, or the owner's. */
export function ChatBubble({ turn }: { turn: ChatTurn }) {
  if (turn.role === "assistant") {
    return (
      <div className="flex items-end gap-2 lg:gap-3">
        <AssistantAvatar />
        <AssistantBubble>{turn.text}</AssistantBubble>
      </div>
    );
  }
  const tone = turn.kind === "skipped" ? "bg-divider text-subtle" : "bg-accent text-white";
  return (
    <p
      className={`m-0 flex items-center gap-2 self-end rounded-[18px] rounded-ee-[6px] px-3.5 py-2.25 text-sm font-semibold lg:rounded-[20px] lg:rounded-ee-[6px] lg:px-4.5 lg:py-2.5 lg:text-[15px] ${tone}`}
    >
      {turn.kind === "link" ? <Icon path={linkIcon} size={16} /> : null}
      {turn.text}
    </p>
  );
}
