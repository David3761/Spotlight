import type { ReactNode } from "react";
import { AppLogo } from "@/components/AppLogo";

/** The props of {@link LoadingFrame}. */
interface LoadingFrameProps {
  /** The screen's content. */
  children: ReactNode;
  /** The business shown in the desktop header, e.g. "Cafeneaua Boema · Cotroceni"; `null` hides it. */
  businessLine: string | null;
}

/** A component that frames the loading screen: the desktop header and the page area. */
export function LoadingFrame({ children, businessLine }: LoadingFrameProps) {
  return (
    <div className="flex min-h-screen flex-col bg-page text-ink">
      <header className="hidden min-h-18 flex-wrap items-center justify-between gap-6 border-b border-border bg-surface px-10 py-3 lg:flex">
        <AppLogo />
        {businessLine && <span className="text-sm font-semibold text-subtle">{businessLine}</span>}
      </header>
      <main className="flex flex-1 flex-col gap-7 px-5 pt-14 pb-8 lg:flex-row lg:flex-wrap lg:items-center lg:justify-center lg:gap-8 lg:p-10">
        {children}
      </main>
    </div>
  );
}
