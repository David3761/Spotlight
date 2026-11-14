import type { ReactNode } from "react";

/** A component that shows the assistant's text in its grey chat bubble. */
export function AssistantBubble({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 max-w-72.5 rounded-[18px] rounded-es-[6px] bg-fill px-3.5 py-2.5 text-sm leading-normal whitespace-pre-wrap lg:max-w-140 lg:rounded-[20px] lg:rounded-es-[6px] lg:px-4.5 lg:py-3 lg:text-[15px]">
      {children}
    </p>
  );
}
