/** Returns a problem count with its Romanian plural, e.g. "1 problemă", "5 probleme", "30 de probleme". */
export function getProblemCountLabel(count: number): string {
  if (count === 1) {
    return "1 problemă";
  }
  const lastTwoDigits = count % 100;
  const needsDe = count !== 0 && (lastTwoDigits === 0 || lastTwoDigits >= 20);
  return `${count} ${needsDe ? "de " : ""}probleme`;
}

/** Returns whether the given date falls on today's date. */
export function isToday(date: Date): boolean {
  return date.toDateString() === new Date().toDateString();
}

/** Returns a date in Romanian with day, month name and year, e.g. "12 noiembrie 2026". */
export function getLongDate(date: Date): string {
  return date.toLocaleDateString("ro-RO", { day: "numeric", month: "long", year: "numeric" });
}

/** Returns "azi" for a date from today, else its long Romanian date. */
export function getDayLabel(date: Date): string {
  return isToday(date) ? "azi" : getLongDate(date);
}
