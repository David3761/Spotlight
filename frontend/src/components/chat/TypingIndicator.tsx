"use client";

import { motion } from "motion/react";
import { AssistantAvatar } from "@/components/chat/AssistantAvatar";

/** A component that shows three bouncing dots while the assistant works on a reply. */
export function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 lg:gap-3">
      <AssistantAvatar />
      <div aria-label="Asistentul scrie" className="flex gap-1.25 rounded-[18px] rounded-es-[6px] bg-fill px-4 py-3.5 lg:rounded-[20px] lg:rounded-es-[6px] lg:px-4.5 lg:py-4">
        {[0, 0.15, 0.3].map((delay) => (
          <motion.span
            key={delay}
            animate={{ y: [0, -4, 0], opacity: [0.35, 1, 0.35] }}
            transition={{ duration: 1, ease: "easeInOut", repeat: Infinity, delay }}
            className="size-1.75 rounded-full bg-muted"
          />
        ))}
      </div>
    </div>
  );
}
