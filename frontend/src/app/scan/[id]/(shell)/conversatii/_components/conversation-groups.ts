import { getLongDate, isToday } from "@/lib/format";
import type { ConversationSummary } from "@/lib/types";

/** The conversations that share a day, under that day's label. */
export interface DayGroup {
  /** The heading: "Azi", "Ieri" or the date. */
  label: string;
  /** The group's conversations, newest first. */
  conversations: ConversationSummary[];
}

/** Returns "Azi", "Ieri" or the long date of a day. */
export function getConversationDayLabel(date: Date): string {
  if (isToday(date)) {
    return "Azi";
  }
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) {
    return "Ieri";
  }
  return getLongDate(date);
}

/** Returns the time of a timestamp as HH:MM. */
export function getTimeLabel(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString("ro-RO", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** Returns the conversations grouped by the day of their last change, keeping their order. */
export function getDayGroups(conversations: ConversationSummary[]): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const conversation of conversations) {
    const label = getConversationDayLabel(new Date(conversation.updated_at));
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
