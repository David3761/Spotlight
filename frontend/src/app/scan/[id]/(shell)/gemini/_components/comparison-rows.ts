import type { CompareRow } from "@/lib/types";

/** The colour family of a comparison tag. */
export type TagTone = "low" | "mid" | "high";

/** A short verdict shown next to the owner's value. */
export interface ComparisonTag {
  /** The verdict text. */
  text: string;
  /** The colour family of the pill. */
  tone: TagTone;
}

/** One row of the comparison table. */
export interface ComparisonRow {
  /** The row's label. */
  label: string;
  /** The owner's value, as text. */
  me: string;
  /** The rivals' values, as text, in rival order. */
  rivals: string[];
  /** The verdict next to the owner's value; `null` when the numbers support none. */
  tag: ComparisonTag | null;
}

/** The text shown when a value is missing. */
const MISSING_TEXT = "–";

/** Returns a rating with a comma decimal, e.g. "4,6". */
export function formatRating(rating: number | null): string {
  return rating === null ? MISSING_TEXT : rating.toFixed(1).replace(".", ",");
}

/** Returns a review or photo count as text, "10+" when the count hit the cap. */
export function getCountText(count: number | null, isCapped: boolean): string {
  if (count === null) {
    return MISSING_TEXT;
  }
  const text = count.toLocaleString("ro-RO");
  return isCapped ? `${text}+` : text;
}

/** Returns "Da" or "Nu" for whether the hours are complete. */
function getHoursText(hoursComplete: boolean | null): string {
  if (hoursComplete === null) {
    return MISSING_TEXT;
  }
  return hoursComplete ? "Da" : "Nu";
}

/** Returns the numbers of the rivals that are set. */
function getKnownNumbers(values: (number | null)[]): number[] {
  return values.filter((value) => value !== null);
}

/** Returns "mult mai puține" when the owner has less than half of the rival with the fewest. */
function getCountTag(me: number | null, rivals: (number | null)[]): ComparisonTag | null {
  const known = getKnownNumbers(rivals);
  if (me === null || known.length === 0) {
    return null;
  }
  return me < Math.min(...known) / 2 ? { text: "mult mai puține", tone: "low" } : null;
}

/** Returns "la fel de bine" when the owner's rating is at most 0.1 below the lowest rival's. */
function getRatingTag(me: number | null, rivals: (number | null)[]): ComparisonTag | null {
  const known = getKnownNumbers(rivals);
  if (me === null || known.length === 0) {
    return null;
  }
  return me >= Math.min(...known) - 0.1 ? { text: "la fel de bine", tone: "high" } : null;
}

/** Returns "lipsesc sărbătorile" when the owner's hours are incomplete and every rival's are complete. */
function getHoursTag(me: boolean | null, rivals: (boolean | null)[]): ComparisonTag | null {
  if (me !== false || !rivals.every((rival) => rival === true)) {
    return null;
  }
  return { text: "lipsesc sărbătorile", tone: "mid" };
}

/** Returns the rivals' lowest and highest rating as "4,5–4,7", or `null` when none is set. */
export function getRatingRangeText(rivals: CompareRow[]): string | null {
  const known = getKnownNumbers(rivals.map((rival) => rival.rating));
  if (known.length === 0) {
    return null;
  }
  return `${formatRating(Math.min(...known))}–${formatRating(Math.max(...known))}`;
}

/** Returns the four comparison rows: reviews, rating, photos and complete hours. */
export function getComparisonRows(me: CompareRow, rivals: CompareRow[]): ComparisonRow[] {
  return [
    {
      label: "Recenzii pe Google",
      me: getCountText(me.review_count, false),
      rivals: rivals.map((rival) => getCountText(rival.review_count, false)),
      tag: getCountTag(me.review_count, rivals.map((rival) => rival.review_count)),
    },
    {
      label: "Notă medie",
      me: formatRating(me.rating),
      rivals: rivals.map((rival) => formatRating(rival.rating)),
      tag: getRatingTag(me.rating, rivals.map((rival) => rival.rating)),
    },
    {
      label: "Fotografii",
      me: getCountText(me.photo_count, me.photo_count_capped),
      rivals: rivals.map((rival) => getCountText(rival.photo_count, rival.photo_count_capped)),
      tag: getCountTag(me.photo_count, rivals.map((rival) => rival.photo_count)),
    },
    {
      label: "Program complet",
      me: getHoursText(me.hours_complete),
      rivals: rivals.map((rival) => getHoursText(rival.hours_complete)),
      tag: getHoursTag(me.hours_complete, rivals.map((rival) => rival.hours_complete)),
    },
  ];
}
