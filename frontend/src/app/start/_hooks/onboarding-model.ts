import { chapterIconPath, iconPath } from "@/components/Icon";
import { getCountLabel } from "@/lib/format";
import type {
  Message,
  OnboardingAnswers,
  OnboardingField,
  OnboardingMessage,
  PlaceCandidate,
  Platform,
  ScanInputs,
} from "@/lib/types";

/** One quick reply: what the owner sees and the value it stores. */
export interface Option<Value extends string> {
  /** The chip label. */
  label: string;
  /** The value stored in the answers. */
  value: Value;
}

/** One line of the business card. */
export interface CardField {
  /** The field label. */
  label: string;
  /** The text shown under the label. */
  value: string;
  /** The SVG path of the field icon. */
  icon: string;
  /** Whether the field is answered, being answered or waiting. */
  status: "done" | "active" | "pending";
}

/** The number of steps in the onboarding. */
export const stepCount = 7;

/** The assistant's first message, which invites the owner to describe the business in their own words. */
export const greeting =
  "Bună! Spune-mi pe scurt despre afacerea ta: cum se numește, ce fel de afacere e și unde te găsesc clienții.";

/** Everything the assistant asks for, in order, before the owner has said anything. */
export const allFields: OnboardingField[] = [
  "business_name",
  "business_type",
  "city",
  "neighborhood",
  "website",
  "google_profile",
  "profile_claimed",
  "has_google_description",
  "last_google_post",
  "social",
  "last_social_post",
  "platforms",
];

/** The answers before the owner has said anything. */
export const emptyAnswers: OnboardingAnswers = {
  business_name: null,
  business_type: null,
  business_type_label_ro: null,
  city: null,
  neighborhood: null,
  has_website: null,
  website_url: null,
  google_choice: null,
  place: null,
  maps_url: null,
  self_report: { profile_claimed: null, has_google_description: null, last_google_post: null, last_social_post: null },
  has_social: null,
  instagram_url: null,
  tiktok_url: null,
  platforms: null,
};

/** The listing platforms the owner can pick. */
export const platformOptions: Option<Platform>[] = [
  { label: "TripAdvisor", value: "tripadvisor" },
  { label: "Glovo", value: "glovo" },
  { label: "Wolt", value: "wolt" },
  { label: "Bolt Food", value: "bolt_food" },
  { label: "Booking", value: "booking" },
  { label: "Booksy", value: "booksy" },
];

/** The answers to a yes/no question. */
const yesNoReplies = ["Da", "Nu", "Nu știu"];

/** The answers to a "when did you last post" question. */
const recencyReplies = ["Luna asta", "Mai demult", "Niciodată", "Nu știu"];

/** The chips under each question; a chip sends its label as the owner's message. */
const quickReplies: Partial<Record<OnboardingField, string[]>> = {
  business_type: ["Cafenea", "Restaurant", "Bar", "Salon", "Hotel", "Magazin", "Altceva"],
  website: ["Nu am site"],
  google_profile: ["Nu am profil Google", "Îl adaug mai târziu"],
  profile_claimed: yesNoReplies,
  has_google_description: yesNoReplies,
  last_google_post: recencyReplies,
  social: ["Nu am Instagram sau TikTok"],
  last_social_post: recencyReplies,
};

/** The hint in the text box for questions that expect something specific. */
const placeholders: Partial<Record<OnboardingField, string>> = {
  business_name: "Numele, tipul afacerii și zona…",
  website: "Adresa site-ului tău…",
  google_profile: "Sau lipește aici linkul de pe Google Maps…",
  social: "Linkuri sau @nume de Instagram și TikTok…",
};

/** The step each answer belongs to, from 1 to 7. */
const fieldSteps: Record<OnboardingField, number> = {
  business_name: 1,
  business_type: 2,
  city: 3,
  neighborhood: 3,
  website: 4,
  google_profile: 5,
  profile_claimed: 5,
  has_google_description: 5,
  last_google_post: 5,
  social: 6,
  last_social_post: 6,
  platforms: 7,
};

/** The card field names, one per step. */
export const stepNames = ["Nume", "Tip", "Locație", "Site", "Google Maps", "Rețele sociale", "Alte platforme"];

/** The SVG path of the cup icon on the type field. */
const cupIcon = "M5 8h12v6a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5zM17 9h1.5a2.5 2.5 0 0 1 0 5H17M8 3v2M11 3v2M14 3v2";

/** The SVG path of the globe icon on the website field. */
const globeIcon = "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18";

/** The SVG path of the map icon on the Google Maps field. */
const mapIcon = "M9 4L3 6.5v13L9 17l6 2.5 6-2.5v-13L15 6.5 9 4zM9 4v13M15 6.5v13";

/** The card field icons, one per step. */
const stepIcons = [iconPath.store, cupIcon, chapterIconPath.profil, globeIcon, mapIcon, chapterIconPath.social, iconPath.grid];

/** Returns the chips under the question being asked, or none. */
export function getQuickReplies(field: OnboardingField | null): string[] {
  return field ? (quickReplies[field] ?? []) : [];
}

/** Returns the hint in the text box for the question being asked. */
export function getPlaceholder(field: OnboardingField | null): string {
  return (field && placeholders[field]) || "Scrie răspunsul tău…";
}

/** Returns whether the platform chips and the button that starts the analysis show: at the last question or after it. */
export function isAtLastStep(field: OnboardingField | null): boolean {
  return field === null || field === "platforms";
}

/** Returns the step, from 1 to 7, of the question being asked; the last step once nothing is missing. */
export function getStepNumber(missing: OnboardingField[]): number {
  return missing.length > 0 ? fieldSteps[missing[0]] : stepCount;
}

/** Returns how many steps have every answer in. */
export function getDoneCount(missing: OnboardingField[]): number {
  const openSteps = new Set(missing.map((field) => fieldSteps[field]));
  return stepCount - openSteps.size;
}

/** Returns the business name's initials: the first letters of its first two words. */
export function getInitials(name: string | null): string {
  const words = (name ?? "").trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

/** Returns the line under a candidate's address: type, rating and review count. */
export function getCandidateMeta(candidate: PlaceCandidate): string {
  const parts = [candidate.type_label_ro];
  if (candidate.rating !== null) {
    parts.push(`${candidate.rating.toString().replace(".", ",")} ★`);
  }
  if (candidate.review_count !== null) {
    parts.push(getCountLabel(candidate.review_count, "recenzie", "recenzii"));
  }
  return parts.join(" · ");
}

/** Returns whether the owner switched on "Nu folosesc altele": an answered, empty platform list. */
export function usesNoOtherPlatforms(answers: OnboardingAnswers): boolean {
  return answers.platforms !== null && answers.platforms.length === 0;
}

/** Returns the platforms' labels, in the order of the chips. */
function getPlatformLabels(platforms: Platform[]): string[] {
  return platformOptions.filter((option) => platforms.includes(option.value)).map((option) => option.label);
}

/** Returns the label of the button that starts the analysis. */
export function getPlatformsCtaLabel(count: number): string {
  if (count === 0) {
    return "Gata, analizează afacerea";
  }
  return `Gata, analizează afacerea (${count} ${count === 1 ? "platformă" : "platforme"})`;
}

/** Returns where the business is, e.g. "Cotroceni, București", or an empty text before it is known. */
function getLocation(answers: OnboardingAnswers): string {
  return [answers.neighborhood, answers.city].filter(Boolean).join(", ");
}

/** Returns the line under the business name on the card, e.g. "Cafenea · Cotroceni, București". */
export function getSubtitle(answers: OnboardingAnswers): string {
  return [answers.business_type_label_ro, getLocation(answers)].filter(Boolean).join(" · ");
}

/** Returns what the card shows for each step, or `null` while that step has no answer. */
function getFieldValues(answers: OnboardingAnswers): (string | null)[] {
  const networks = [answers.instagram_url ? "Instagram" : null, answers.tiktok_url ? "TikTok" : null].filter(Boolean);
  const googleValues = { place: answers.place?.address ?? null, none: "Fără profil Google", later: "Îl adaug mai târziu" };
  let site: string | null = null;
  if (answers.has_website !== null) {
    site = answers.has_website ? (answers.website_url?.replace(/^https?:\/\//, "") ?? null) : "Fără site";
  }
  let social: string | null = null;
  if (answers.has_social !== null) {
    social = answers.has_social ? networks.join(", ") || null : "Fără rețele";
  }
  let platforms: string | null = null;
  if (answers.platforms !== null) {
    platforms = usesNoOtherPlatforms(answers) ? "Nu folosesc altele" : getPlatformLabels(answers.platforms).join(", ");
  }
  return [
    answers.business_name,
    answers.business_type_label_ro,
    getLocation(answers) || null,
    site,
    answers.google_choice ? googleValues[answers.google_choice] : null,
    social,
    platforms,
  ];
}

/** Returns the business card's seven fields: done when every answer of the step is in, active for the question asked. */
export function getCardFields(answers: OnboardingAnswers, missing: OnboardingField[]): CardField[] {
  const values = getFieldValues(answers);
  const openSteps = new Set(missing.map((field) => fieldSteps[field]));
  const askedStep = missing.length > 0 ? fieldSteps[missing[0]] : null;
  return stepNames.map((label, index) => {
    const step = index + 1;
    const value = values[index];
    if (!openSteps.has(step)) {
      return { label, value: value ?? "", icon: stepIcons[index], status: "done" };
    }
    if (step === askedStep) {
      return { label, value: value ?? "Completăm acum…", icon: stepIcons[index], status: "active" };
    }
    return { label, value: value ?? "Urmează", icon: stepIcons[index], status: "pending" };
  });
}

/** Returns the request that starts the scan from the owner's answers. */
export function getScanInputs(answers: OnboardingAnswers): ScanInputs {
  return {
    business_name: answers.business_name ?? "",
    business_type: answers.business_type ?? "altceva",
    business_type_label_ro: answers.business_type_label_ro ?? "",
    city: answers.city ?? "",
    neighborhood: answers.neighborhood ?? "",
    has_website: answers.has_website === true,
    website_url: answers.has_website ? answers.website_url : null,
    place_id: answers.place?.place_id ?? null,
    maps_url: answers.maps_url,
    no_google_profile: answers.google_choice === "none",
    instagram_url: answers.instagram_url,
    tiktok_url: answers.tiktok_url,
    platforms: answers.platforms,
    self_report: answers.self_report,
  };
}

/** Returns the owner's message that answers the platforms question with the chips. */
export function getPlatformsMessage(answers: OnboardingAnswers): OnboardingMessage {
  if (answers.platforms === null) {
    return { role: "user", text: "Sar peste" };
  }
  if (usesNoOtherPlatforms(answers)) {
    return { role: "user", text: "Nu folosesc altele" };
  }
  return { role: "user", text: getPlatformLabels(answers.platforms).join(", ") };
}

/** Returns the conversation as contract messages, one second apart from `startedAt`. */
export function getMessages(messages: OnboardingMessage[], startedAt: Date): Message[] {
  return messages.map((message, index) => ({
    id: `onboarding-${index + 1}`,
    role: message.role,
    text: message.text,
    created_at: new Date(startedAt.getTime() + index * 1000).toISOString(),
    action: null,
    chips: [],
  }));
}
