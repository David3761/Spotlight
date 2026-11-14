/** A score's colour tier: under 40, 40–69, or 70 and over. */
export type ScoreTier = "low" | "mid" | "high";

/** Returns the colour tier of a score. */
export function getScoreTier(score: number): ScoreTier {
  if (score < 40) {
    return "low";
  }
  return score < 70 ? "mid" : "high";
}
