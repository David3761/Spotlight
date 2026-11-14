/** The design system's button looks: colours, shape and weight. Sizes are set per use. */
export const buttonVariant = {
  primary: "inline-flex items-center justify-center gap-2 rounded-full bg-accent font-bold text-white hover:bg-accent-hover",
  outline: "inline-flex items-center justify-center gap-2 rounded-full border border-accent-outline bg-surface font-bold text-accent-strong",
  soft: "inline-flex items-center justify-center gap-2 rounded-full bg-fill font-bold text-body",
};

/** The pressable chip looks (tones, quick replies, platforms), pressed or not. */
export const chipVariant = {
  pressed: "rounded-full border-2 border-accent bg-accent-soft font-bold text-accent-strong",
  idle: "rounded-full border border-border bg-surface font-semibold text-body",
};
