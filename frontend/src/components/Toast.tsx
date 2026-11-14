"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Icon, iconPath } from "@/components/Icon";

/** How long a toast stays on screen. */
const TOAST_DURATION_MS = 3000;

/** What a toast says. */
export interface ToastContent {
  /** The bold part, e.g. "+6 puncte". */
  title: string;
  /** The lighter part after it, e.g. "Rețele sociale a urcat la 61". */
  detail?: string;
}

/** A component that shows a points toast that rises in, stays a few seconds, then calls `onDismiss`. */
export function Toast({ toast, onDismiss }: { toast: ToastContent | null; onDismiss: () => void }) {
  useEffect(() => {
    if (!toast) {
      return;
    }
    const timer = window.setTimeout(onDismiss, TOAST_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [toast, onDismiss]);

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          role="status"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          className="fixed bottom-27 left-1/2 z-50 flex h-13 -translate-x-1/2 items-center gap-2.5 rounded-full bg-ink ps-2 pe-5.5 text-[15px] font-bold whitespace-nowrap text-white shadow-[0_12px_28px_rgba(15,23,42,0.25)] lg:bottom-8 lg:left-[calc(50%+140px)]"
        >
          <span className="flex size-8.5 items-center justify-center rounded-full bg-high">
            <Icon path={iconPath.arrowUp} size={17} strokeWidth={3} />
          </span>
          {toast.title}
          {toast.detail && <span className="font-medium text-bar">· {toast.detail}</span>}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
