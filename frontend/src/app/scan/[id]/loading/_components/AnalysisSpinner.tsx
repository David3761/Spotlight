"use client";

import { motion } from "motion/react";
import { iconPath } from "@/components/Icon";

/** The ring's stroke thickness. */
const STROKE = 12;

/** The props of {@link AnalysisSpinner}. */
interface AnalysisSpinnerProps {
  /** The spinner's width and height. */
  size: number;
  /** The radius of the ring's centre line. */
  radius: number;
  /** The width and height of the star in the middle. */
  starSize: number;
}

/** A component that shows a quarter arc turning around a floating star while the analysis runs. */
export function AnalysisSpinner({ size, radius, starSize }: AnalysisSpinnerProps) {
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true" className="absolute inset-0">
        <circle cx={center} cy={center} r={radius} fill="none" strokeWidth={STROKE} className="stroke-accent-soft" />
      </svg>
      <motion.svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden="true"
        className="absolute inset-0"
        animate={{ rotate: 360 }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
      >
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={`${circumference / 4} ${(circumference * 3) / 4}`}
          className="stroke-accent"
        />
      </motion.svg>
      <motion.div
        className="absolute inset-0 flex items-center justify-center"
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      >
        <svg width={starSize} height={starSize} viewBox="0 0 24 24" aria-hidden="true">
          <path d={iconPath.sparkle} className="fill-accent" />
        </svg>
      </motion.div>
    </div>
  );
}
