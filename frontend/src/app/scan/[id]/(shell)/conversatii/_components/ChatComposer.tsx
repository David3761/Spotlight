import type { SubmitEvent } from "react";
import { Icon, iconPath } from "@/components/Icon";
import { chipVariant } from "@/components/button-styles";

/** The quick messages offered above the input on desktop. */
const quickMessages = ["Marchează ceva ca rezolvat", "Ce fac acum?", "Scrie-mi un text"];

/** The props of {@link ChatComposer}. */
interface ChatComposerProps {
  /** The text in the input. */
  value: string;
  /** When `true`, a request is running and nothing can be sent. */
  isBusy: boolean;
  /** Called with the new text when the owner types. */
  onChange: (value: string) => void;
  /** Called with the typed text to send. */
  onSend: (text: string) => void;
  /** Called with a quick message to send, leaving the typed text alone. */
  onQuickMessage: (text: string) => void;
}

/** A component that offers quick messages (desktop), the message input and the send button. */
export function ChatComposer({ value, isBusy, onChange, onSend, onQuickMessage }: ChatComposerProps) {
  const canSend = !isBusy && value.trim() !== "";

  /** Sends the typed text. */
  const handleSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (canSend) {
      onSend(value.trim());
    }
  };

  return (
    <div className="flex flex-col gap-2.5 border-t border-divider px-3 pt-2.5 pb-6.5 lg:px-5 lg:pt-3 lg:pb-4.5">
      <div className="hidden flex-wrap gap-2 lg:flex">
        {quickMessages.map((message) => (
          <button
            key={message}
            type="button"
            disabled={isBusy}
            onClick={() => onQuickMessage(message)}
            className={`${chipVariant.idle} h-9 px-3.5 text-[13px] disabled:opacity-60`}
          >
            {message}
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex items-center gap-2.5 lg:gap-3">
        <label htmlFor="chatInput" className="sr-only">
          Mesaj pentru asistent
        </label>
        <input
          id="chatInput"
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Scrie un mesaj…"
          className="min-h-12 min-w-0 flex-1 rounded-full bg-fill px-4.5 text-[15px] text-ink outline-none lg:min-h-13 lg:px-5"
        />
        <button
          type="submit"
          aria-label="Trimite"
          disabled={!canSend}
          className="flex size-12 flex-none items-center justify-center rounded-full bg-accent text-white disabled:opacity-60 lg:size-13"
        >
          <Icon path={iconPath.arrowUp} size={20} strokeWidth={2.2} />
        </button>
      </form>
    </div>
  );
}
