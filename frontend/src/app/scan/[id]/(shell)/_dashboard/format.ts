/** Returns a problem count with its Romanian plural, e.g. "1 problemă", "5 probleme", "30 de probleme". */
export function getProblemCountLabel(count: number): string {
  if (count === 1) {
    return "1 problemă";
  }
  const lastTwoDigits = count % 100;
  const isShortForm = count === 0 || (lastTwoDigits >= 2 && lastTwoDigits <= 19);
  return isShortForm ? `${count} probleme` : `${count} de probleme`;
}

/** Returns "azi" for a timestamp from today, else its date in Romanian. */
export function getDayLabel(timestamp: string): string {
  const date = new Date(timestamp);
  if (date.toDateString() === new Date().toDateString()) {
    return "azi";
  }
  return date.toLocaleDateString("ro-RO", { day: "numeric", month: "long", year: "numeric" });
}
