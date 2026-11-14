"use client";

import { motion } from "motion/react";

/** The three skeleton lines' widths and animation delays. */
const lines = [
  { width: "w-[92%]", delay: 0 },
  { width: "w-full", delay: 0.15 },
  { width: "w-3/4", delay: 0.3 },
];

/** A component that shows skeleton lines and a bouncing-dots label while something is being written or loaded. */
export function LoadingBlock({ label }: { label: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex min-h-39 flex-col gap-3 rounded-[18px] border-2 border-border bg-surface p-4 lg:p-4.5"
    >
      {lines.map((line) => (
        <motion.span
          key={line.delay}
          animate={{ opacity: [1, 0.45, 1] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut", delay: line.delay }}
          className={`h-3.5 rounded-[7px] bg-ring-track ${line.width}`}
        />
      ))}
      <span className="mt-auto flex items-center gap-2 text-[13px] font-bold text-accent-hover">
        <span className="flex gap-1" aria-hidden="true">
          {lines.map((line) => (
            <motion.span
              key={line.delay}
              animate={{ y: [0, -4, 0], opacity: [0.35, 1, 0.35] }}
              transition={{ duration: 1, repeat: Infinity, ease: "easeInOut", delay: line.delay }}
              className="size-1.5 rounded-full bg-accent"
            />
          ))}
        </span>
        {label}
      </span>
    </div>
  );
}
