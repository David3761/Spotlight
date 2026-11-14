"use client";

import { AnimatePresence, motion } from "motion/react";
import { Dialog } from "radix-ui";
import { Icon, iconPath } from "@/components/Icon";
import type { Problem } from "@/lib/types";
import { useIsDesktop } from "../_hooks/use-is-desktop";
import { DevExportPanel } from "./DevExportPanel";
import { GenerateTextPanel } from "./GenerateTextPanel";
import { InfoPagePanel } from "./InfoPagePanel";
import { StepsPanel } from "./StepsPanel";

/** How long the panel takes to slide in or out, in seconds. */
const SLIDE_DURATION = 0.28;

/** The easing of the slide. */
const SLIDE_EASING = [0.2, 0.8, 0.2, 1] as const;

/** A component that shows the body that matches the problem's fix panel. */
function FixPanelBody({ scanId, problem, onResolve }: { scanId: string; problem: Problem; onResolve: () => void }) {
  switch (problem.fix.panel) {
    case "generate_text":
      return <GenerateTextPanel scanId={scanId} problem={problem} onResolve={onResolve} />;
    case "info_page":
      return <InfoPagePanel scanId={scanId} onResolve={onResolve} />;
    case "dev_export":
      return <DevExportPanel scanId={scanId} onResolve={onResolve} />;
    case "steps":
      return <StepsPanel problem={problem} onResolve={onResolve} />;
  }
}

/** A component that shows a problem's fix in a side panel on desktop or a bottom sheet on mobile, over a dimmed backdrop. */
export function FixPanel({
  scanId,
  problem,
  onClose,
  onResolve,
}: {
  scanId: string;
  problem: Problem | null;
  onClose: () => void;
  onResolve: (problem: Problem) => void;
}) {
  const isDesktop = useIsDesktop();
  const offscreen = isDesktop ? { x: 48, opacity: 0 } : { y: 60, opacity: 0 };
  const onscreen = isDesktop ? { x: 0, opacity: 1 } : { y: 0, opacity: 1 };
  const transition = { duration: SLIDE_DURATION, ease: SLIDE_EASING };

  return (
    <Dialog.Root
      open={problem !== null}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      <AnimatePresence>
        {problem && (
          <Dialog.Portal forceMount>
            <Dialog.Overlay asChild forceMount>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.22 }}
                className="fixed inset-0 z-40 bg-backdrop"
              />
            </Dialog.Overlay>
            <Dialog.Content asChild forceMount aria-describedby={undefined}>
              <motion.div
                initial={offscreen}
                animate={onscreen}
                exit={offscreen}
                transition={transition}
                className={`fixed inset-x-0 bottom-0 z-50 flex max-h-[92dvh] flex-col rounded-t-[28px] bg-surface shadow-[0_-16px_40px_rgba(15,23,42,0.18)] lg:inset-y-0 lg:start-auto lg:end-0 lg:max-h-none lg:max-w-full lg:rounded-s-[28px] lg:rounded-t-none lg:shadow-[-24px_0_48px_rgba(15,23,42,0.16)] ${
                  problem.fix.panel === "generate_text" || problem.fix.panel === "steps" ? "lg:w-130" : "lg:w-160"
                }`}
              >
                <div className="flex justify-center pt-2.5 pb-0.5 lg:hidden" aria-hidden="true">
                  <span className="h-1.25 w-10 rounded-[3px] bg-bar" />
                </div>
                <div className="flex items-start gap-3 px-5 pt-2 pb-3.5 lg:gap-4 lg:border-b lg:border-divider lg:px-7 lg:pt-6 lg:pb-4.5">
                  <div className="flex min-w-0 flex-1 flex-col gap-1.5 lg:gap-2">
                    <span className="flex h-6.5 items-center self-start rounded-full bg-high-tint px-2.5 text-xs font-extrabold text-high-text lg:h-7 lg:px-3 lg:text-[13px]">
                      <span className="hidden lg:inline">{problem.chapter_name_ro} · </span>+{problem.points} puncte
                    </span>
                    <Dialog.Title className="text-xl font-extrabold tracking-[-0.01em] lg:text-[22px]">
                      {problem.title_ro}
                    </Dialog.Title>
                  </div>
                  <Dialog.Close
                    aria-label="Închide"
                    className="flex size-11 shrink-0 items-center justify-center rounded-full bg-fill text-body"
                  >
                    <Icon path={iconPath.cross} size={20} strokeWidth={2.2} />
                  </Dialog.Close>
                </div>
                <FixPanelBody scanId={scanId} problem={problem} onResolve={() => onResolve(problem)} />
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}
