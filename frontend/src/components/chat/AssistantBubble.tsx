import type { ReactNode } from "react";

/** A component that shows the assistant's text in its grey chat bubble. */
export function AssistantBubble({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <p
      className={`m-0 rounded-[18px] rounded-es-md bg-fill px-3.5 py-2.5 text-sm leading-normal whitespace-pre-wrap lg:max-w-140 lg:rounded-[20px] lg:rounded-es-md lg:px-4.5 lg:py-3 lg:text-[15px] ${className}`}
    >
      {children}
    </p>
  );
}
