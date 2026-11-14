/** Returns the Romanian count of open problems, e.g. "1 problemă de rezolvat" or "20 de probleme de rezolvat". */
export function getProblemCountLabel(count: number): string {
  if (count === 1) {
    return "1 problemă de rezolvat";
  }
  const lastTwoDigits = count % 100;
  const needsDe = count !== 0 && (lastTwoDigits === 0 || lastTwoDigits >= 20);
  return `${count} ${needsDe ? "de " : ""}probleme de rezolvat`;
}
