/** Returns a problem count with its Romanian plural, e.g. "1 problemă", "5 probleme", "30 de probleme". */
export function getProblemCountLabel(count: number): string {
  if (count === 1) {
    return "1 problemă";
  }
  const lastTwoDigits = count % 100;
  const needsDe = count !== 0 && (lastTwoDigits === 0 || lastTwoDigits >= 20);
  return `${count} ${needsDe ? "de " : ""}probleme`;
}

/** Returns whether the date falls on the same day as `now`. */
export function isToday(date: Date, now = new Date()): boolean {
  return date.toDateString() === now.toDateString();
}

/** Returns a date in Romanian with day and month name, plus the year when it isn't the current one, e.g. "12 noiembrie". */
export function getLongDate(date: Date, now = new Date()): string {
  const isThisYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString("ro-RO", isThisYear ? { day: "numeric", month: "long" } : { day: "numeric", month: "long", year: "numeric" });
}

/** Returns "azi" for a timestamp from today, its long Romanian date otherwise, or `null` when it can't be read. */
export function getDayLabel(timestamp: string): string | null {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return isToday(date) ? "azi" : getLongDate(date);
}
