import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { AssistantBubble } from "@/components/chat/AssistantBubble";
import type { OnboardingMessage } from "@/lib/types";

/** A component that shows one bubble of the conversation: the assistant's with its avatar, or the owner's. */
export function ChatBubble({ message }: { message: OnboardingMessage }) {
  if (message.role === "assistant") {
    return (
      <div className="flex items-end gap-2 lg:gap-3">
        <AssistantAvatar />
        <AssistantBubble>{message.text}</AssistantBubble>
      </div>
    );
  }
  return (
    <p className="m-0 self-end rounded-[18px] rounded-ee-md bg-accent px-3.5 py-2.25 text-sm font-semibold wrap-break-word text-white lg:rounded-[20px] lg:rounded-ee-md lg:px-4.5 lg:py-2.5 lg:text-[15px]">
      {message.text}
    </p>
  );
}
