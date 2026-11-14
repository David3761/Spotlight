"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { motion } from "motion/react";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";
import { AssistantBubble } from "@/components/chat/AssistantBubble";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { Icon, iconPath } from "@/components/Icon";
import { useLoadedScan } from "@/components/ScanShell";
import { buttonVariant } from "@/components/button-styles";
import type { ActionOption, Message, ProposedAction } from "@/lib/types";
import { getChapterOfCheck } from "./chat-data";

/** The props of {@link ChatMessages}. */
interface ChatMessagesProps {
  /** The messages, oldest first. */
  messages: Message[];
  /** When `true`, the assistant is working on a reply and the typing indicator shows. */
  isTyping: boolean;
  /** When `true`, a request is running and the buttons under the messages are disabled. */
  isBusy: boolean;
  /** Called with the text of a quick reply the owner picked. */
  onReply: (text: string) => void;
  /** Called with the action and the option the owner picked. */
  onOption: (actionId: string, optionId: string) => void;
}

/** The looks of the buttons under the messages, which share their size. */
const replyButtonSize = "h-11 px-3.5 text-sm disabled:opacity-60 lg:px-4.5";

/** The look of a neutral button under a message, e.g. "Nu încă". */
const neutralButton = `rounded-full border border-border bg-surface font-semibold text-subtle ${replyButtonSize}`;

/** A component that shows the conversation: bubbles, action cards, quick replies and the typing indicator. */
export function ChatMessages({ messages, isTyping, isBusy, onReply, onOption }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages.length, isTyping]);

  return (
    <div ref={scrollRef} className="flex min-h-0 flex-1 flex-col overflow-y-auto p-4 lg:px-7 lg:py-6">
      <div aria-live="polite" className="mt-auto flex flex-col gap-2.5 lg:gap-3.5">
        {messages.map((message, index) => (
          <MessageView
            key={message.id}
            message={message}
            isLast={index === messages.length - 1}
            isBusy={isBusy}
            onReply={onReply}
            onOption={onOption}
          />
        ))}
        {isTyping && <TypingIndicator />}
      </div>
    </div>
  );
}

/** A component that shows one message: the bubble, then its action and quick replies. */
function MessageView({
  message,
  isLast,
  isBusy,
  onReply,
  onOption,
}: {
  message: Message;
  isLast: boolean;
  isBusy: boolean;
  onReply: (text: string) => void;
  onOption: (actionId: string, optionId: string) => void;
}) {
  if (message.role === "user") {
    return (
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.26 }}
        className="max-w-75 self-end rounded-[18px] rounded-ee-[6px] bg-accent px-3.5 py-2.5 text-sm leading-normal whitespace-pre-wrap text-white lg:max-w-130 lg:rounded-[20px] lg:rounded-ee-[6px] lg:px-4.5 lg:py-2.75 lg:text-[15px] lg:font-medium"
      >
        {message.text}
      </motion.p>
    );
  }

  const action = message.action;
  const showChips = isLast && !isBusy && message.chips.length > 0;
  const hasExtras = action !== null && action.status !== "undone" && action.status !== "declined";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26 }}
      className={`flex gap-2 lg:gap-3 ${hasExtras || showChips ? "items-start" : "items-end"}`}
    >
      <AssistantAvatar />
      <div className="flex min-w-0 flex-col gap-2 lg:gap-2.5">
        <AssistantBubble>{message.text}</AssistantBubble>
        {action?.status === "pending" && (
          <div className="flex flex-wrap gap-1.5 lg:gap-2">
            {action.options.map((option, index) => (
              <OptionButton key={option.id} option={option} isFirst={index === 0} isDisabled={isBusy} action={action} onOption={onOption} />
            ))}
          </div>
        )}
        {action?.status === "confirmed" && <ConfirmedCard action={action} isDisabled={isBusy} onUndo={onOption} />}
        {showChips && (
          <div className="flex flex-wrap gap-1.5 lg:gap-2">
            {message.chips.map((chip, index) => (
              <button
                key={chip}
                type="button"
                disabled={isBusy}
                onClick={() => onReply(chip)}
                className={index === 0 ? `${buttonVariant.primary} ${replyButtonSize}` : neutralButton}
              >
                {chip}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

/** A component that shows one option of a pending action as a button. */
function OptionButton({
  option,
  action,
  isFirst,
  isDisabled,
  onOption,
}: {
  option: ActionOption;
  action: ProposedAction;
  isFirst: boolean;
  isDisabled: boolean;
  onOption: (actionId: string, optionId: string) => void;
}) {
  const isDecline = option.check_ids.length === 0;
  const look = isDecline ? neutralButton : `${isFirst ? buttonVariant.primary : buttonVariant.outline} ${replyButtonSize}`;

  return (
    <button type="button" disabled={isDisabled} onClick={() => onOption(action.action_id, option.id)} className={look}>
      {option.label_ro}
    </button>
  );
}

/** A component that shows the problems the owner marked as fixed, with their points and an undo button. */
function ConfirmedCard({
  action,
  isDisabled,
  onUndo,
}: {
  action: ProposedAction;
  isDisabled: boolean;
  onUndo: (actionId: string, optionId: string) => void;
}) {
  const { report } = useLoadedScan();
  const items = action.items.filter((item) => action.confirmed_check_ids.includes(item.check_id));

  return (
    <div className="flex flex-col gap-2 rounded-[18px] border-2 border-high-line bg-surface px-3.5 py-3 lg:gap-2.5 lg:rounded-[20px] lg:px-4.5 lg:py-4">
      <div className="flex items-center gap-2 lg:gap-2.5">
        <motion.span
          initial={{ scale: 0.4 }}
          animate={{ scale: [0.4, 1.2, 1] }}
          transition={{ duration: 0.42 }}
          className="flex size-6 items-center justify-center rounded-full bg-high text-white lg:size-7"
        >
          <Icon path={iconPath.check} size={14} strokeWidth={3} />
        </motion.span>
        <span className="flex-1 text-sm font-extrabold lg:text-[15px]">
          {items.length === 1 ? "Am marcat ca rezolvată" : "Am marcat ca rezolvate"}
        </span>
        <button
          type="button"
          disabled={isDisabled}
          onClick={() => onUndo(action.action_id, "undo")}
          className="h-9 rounded-full bg-fill px-2.5 text-xs font-bold text-body disabled:opacity-60 lg:px-3 lg:text-[13px]"
        >
          Anulează
        </button>
      </div>
      {items.map((item) => (
        <ConfirmedRow key={item.check_id} title={item.title_ro} points={item.points}>
          {getChapterOfCheck(report, item.check_id)?.name_ro}
        </ConfirmedRow>
      ))}
      <span className="text-[11px] text-subtle lg:text-xs">Verificăm automat pe Google la următoarea analiză.</span>
    </div>
  );
}

/** A component that shows one confirmed problem with its chapter (desktop only) and points. */
function ConfirmedRow({ title, points, children }: { title: string; points: number; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-high-wash px-2.5 py-2 lg:gap-2.5 lg:rounded-[14px] lg:px-3 lg:py-2.5">
      <Icon path={iconPath.check} size={18} strokeWidth={2.6} className="hidden flex-none text-high-text lg:block" />
      <span className="flex flex-1 flex-col gap-px">
        <span className="text-[13px] leading-[1.35] font-bold lg:text-sm">{title}</span>
        <span className="hidden text-xs text-subtle lg:block">{children}</span>
      </span>
      <span className="text-[13px] font-extrabold text-high-text lg:text-sm">+{points}</span>
    </div>
  );
}
