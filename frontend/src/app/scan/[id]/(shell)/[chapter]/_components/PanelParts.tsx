import type { ReactNode } from "react";
import { buttonVariant } from "@/components/button-styles";

/** A component that holds the scrolling content of a fix panel. */
export function PanelBody({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`flex min-h-0 flex-1 flex-col gap-5 overflow-auto px-5 py-4 lg:px-7 lg:py-5.5 ${className}`}>{children}</div>;
}

/** A component that holds the action buttons pinned to the bottom of a fix panel. */
export function PanelFooter({ children }: { children: ReactNode }) {
  return <div className="flex flex-col gap-2.5 border-t border-divider px-5 pt-3 pb-7 lg:px-7 lg:pt-4 lg:pb-6">{children}</div>;
}

/** A component that shows the „Am rezolvat” button every fix panel ends with. */
export function ResolveButton({ onResolve }: { onResolve: () => void }) {
  return (
    <button type="button" onClick={onResolve} className={`${buttonVariant.outline} h-12.5 w-full text-base lg:h-13`}>
      Am rezolvat
    </button>
  );
}
