"use client";

import { useEffect, useRef, useState } from "react";
import { getScoreTier } from "@/lib/score-tier";

/** How long the ring takes to fill to a new score. */
const FILL_DURATION_MS = 1100;

/** How long the scale bump lasts after the score rises. */
const BUMP_DURATION_MS = 380;

/** The delay before the first fill, when the ring mounts with {@link ScoreRingProps.animateFrom}. */
const MOUNT_DELAY_MS = 350;

/** The delay before a fill caused by a score change. */
const UPDATE_DELAY_MS = 120;

/** The ring stroke colour of each score tier. */
const tierStroke = { low: "stroke-low", mid: "stroke-mid", high: "stroke-high" };

/** The props of {@link ScoreRing}. */
interface ScoreRingProps {
  /** The score to show; `null` shows an empty ring with a dash. */
  score: number | null;
  /** The ring's width and height. */
  size: number;
  /** The stroke thickness; defaults to a tenth of the size. */
  thick?: number;
  /** When `true`, "din 100" is shown under the number. */
  showMax?: boolean;
  /** The score the ring fills from when it mounts. */
  animateFrom?: number;
}

/** A component that shows a score inside a coloured ring that fills when the score changes. */
export function ScoreRing({ score, size, thick, showMax = false, animateFrom }: ScoreRingProps) {
  const [shown, setShown] = useState(animateFrom ?? score ?? 0);
  const [isBumped, setIsBumped] = useState(false);
  const shownRef = useRef(shown);
  const isFirstFillRef = useRef(true);

  useEffect(() => {
    const delay = isFirstFillRef.current ? MOUNT_DELAY_MS : UPDATE_DELAY_MS;
    isFirstFillRef.current = false;
    const from = shownRef.current;
    if (score === null || from === score) {
      return;
    }
    let frame = 0;
    let bumpTimer = 0;
    const startTimer = window.setTimeout(() => {
      const start = performance.now();
      const step = (now: number) => {
        const progress = Math.min(1, (now - start) / FILL_DURATION_MS);
        const value = from + (score - from) * (1 - Math.pow(1 - progress, 3));
        shownRef.current = value;
        setShown(value);
        if (progress < 1) {
          frame = requestAnimationFrame(step);
        } else if (score > from) {
          setIsBumped(true);
          bumpTimer = window.setTimeout(() => setIsBumped(false), BUMP_DURATION_MS);
        }
      };
      frame = requestAnimationFrame(step);
    }, delay);
    return () => {
      window.clearTimeout(startTimer);
      window.clearTimeout(bumpTimer);
      cancelAnimationFrame(frame);
    };
  }, [score]);

  const thickness = thick ?? Math.max(3, Math.round(size * 0.1));
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const rounded = Math.round(shown);
  const label = score === null ? "Scor necunoscut" : `Scor ${score} din 100`;

  return (
    <div
      role="img"
      aria-label={label}
      className="relative shrink-0 text-ink transition-transform duration-[380ms] ease-[cubic-bezier(.3,1.6,.5,1)]"
      style={{ width: size, height: size, transform: isBumped ? "scale(1.06)" : "scale(1)" }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true" className="block -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={thickness} className="stroke-ring-track" />
        {score !== null && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={thickness}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - shown / 100)}
            className={tierStroke[getScoreTier(rounded)]}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-extrabold leading-none tracking-[-0.03em] tabular-nums"
          style={{ fontSize: Math.round(size * (showMax ? 0.28 : 0.3)) }}
        >
          {score === null ? "–" : rounded}
        </span>
        {showMax && (
          <span className="mt-1 font-semibold text-muted" style={{ fontSize: Math.max(11, Math.round(size * 0.075)) }}>
            din 100
          </span>
        )}
      </div>
    </div>
  );
}
