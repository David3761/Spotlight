import type { ConversationSummary } from "@/lib/types";

/** The conversations that share a day, under that day's label. */
export interface DayGroup {
  /** The heading: "Azi", "Ieri" or the date. */
  label: string;
  /** The group's conversations, newest first. */
  conversations: ConversationSummary[];
}

/** The number of milliseconds in a day. */
const DAY_MS = 86_400_000;

/** Returns midnight at the start of a date's day. */
function getStartOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

/** Returns "Azi", "Ieri" or the date of a day, relative to `now`. */
export function getDayLabel(date: Date, now: Date): string {
  const daysAgo = Math.round((getStartOfDay(now) - getStartOfDay(date)) / DAY_MS);
  if (daysAgo === 0) {
    return "Azi";
  }
  if (daysAgo === 1) {
    return "Ieri";
  }
  return date.toLocaleDateString("ro-RO", {
    day: "numeric",
    month: "long",
    year: date.getFullYear() === now.getFullYear() ? undefined : "numeric",
  });
}

/** Returns the time of a timestamp as HH:MM. */
export function getTimeLabel(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString("ro-RO", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** Returns the conversations grouped by the day of their last change, keeping their order. */
export function getDayGroups(conversations: ConversationSummary[], now: Date): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const conversation of conversations) {
    const label = getDayLabel(new Date(conversation.updated_at), now);
    const last = groups[groups.length - 1];
    if (last?.label === label) {
      last.conversations.push(conversation);
    } else {
      groups.push({ label, conversations: [conversation] });
    }
  }
  return groups;
}

/** Returns whether a conversation's title or preview contains the search text. */
export function getMatchesSearch(conversation: ConversationSummary, search: string): boolean {
  const needle = search.trim().toLocaleLowerCase("ro");
  if (needle === "") {
    return true;
  }
  return `${conversation.title} ${conversation.preview}`.toLocaleLowerCase("ro").includes(needle);
}
