import { chapterIconPath, iconPath } from "@/components/Icon";
import type {
  BusinessType,
  Message,
  PlaceCandidate,
  Platform,
  PostRecency,
  ScanInputs,
  SelfReport,
  YesNoUnknown,
} from "@/lib/types";

/** The question the owner is answering now. */
export type Phase =
  | "name"
  | "type"
  | "typeOther"
  | "location"
  | "website"
  | "websiteUrl"
  | "maps"
  | "candidates"
  | "mapsError"
  | "profileClaimed"
  | "googleDescription"
  | "googlePost"
  | "social"
  | "socialPost"
  | "platforms";

/** A phase whose question is answered with one quick reply that fills a self-report field. */
export type SelfReportPhase = "profileClaimed" | "googleDescription" | "googlePost" | "socialPost";

/** How the owner answered the Google Maps step. */
export type GoogleChoice = "place" | "none" | "later";

/** How a chat bubble looks. */
export type TurnKind = "text" | "link" | "skipped";

/** One bubble of the scripted conversation. */
export interface ChatTurn {
  /** Who says it. */
  role: "assistant" | "user";
  /** The bubble text. */
  text: string;
  /** How the bubble looks. */
  kind: TurnKind;
}

/** Everything the owner has answered so far. */
export interface Answers {
  /** The business name. */
  businessName: string;
  /** The picked business type, `null` until picked. */
  businessType: BusinessType | null;
  /** The type as picked or typed. */
  typeLabel: string;
  /** The city. */
  city: string;
  /** The neighbourhood. */
  neighborhood: string;
  /** Whether the business has a website, `null` until answered. */
  hasWebsite: boolean | null;
  /** The website URL. */
  websiteUrl: string | null;
  /** How the Google Maps step was answered, `null` until answered. */
  googleChoice: GoogleChoice | null;
  /** The picked Google place. */
  place: PlaceCandidate | null;
  /** The pasted Google Maps link. */
  mapsUrl: string | null;
  /** The self-reported answers. */
  selfReport: SelfReport;
  /** Whether the social step was answered. */
  hasAnsweredSocial: boolean;
  /** The Instagram profile URL. */
  instagramUrl: string | null;
  /** The TikTok profile URL. */
  tiktokUrl: string | null;
  /** The chosen listing platforms. */
  platforms: Platform[];
  /** Whether the owner said they use no other platforms. */
  usesNoOtherPlatforms: boolean;
}

/** One quick reply: what the owner sees and the value it stores. */
export interface Option<Value extends string> {
  /** The chip label, also the owner's chat bubble. */
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

/** The business types the owner can pick. */
export const businessTypeOptions: Option<BusinessType>[] = [
  { label: "Cafenea", value: "cafenea" },
  { label: "Restaurant", value: "restaurant" },
  { label: "Bar", value: "bar" },
  { label: "Salon", value: "salon" },
  { label: "Hotel", value: "hotel" },
  { label: "Magazin", value: "magazin" },
  { label: "Altceva", value: "altceva" },
];

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
const yesNoOptions: Option<YesNoUnknown>[] = [
  { label: "Da", value: "da" },
  { label: "Nu", value: "nu" },
  { label: "Nu știu", value: "nu_stiu" },
];

/** The answers to a "when did you last post" question. */
const recencyOptions: Option<PostRecency>[] = [
  { label: "Luna asta", value: "luna_asta" },
  { label: "Mai demult", value: "mai_demult" },
  { label: "Niciodată", value: "niciodata" },
  { label: "Nu știu", value: "nu_stiu" },
];

/** The self-report questions: the field each one fills, its answers and the phase after it. */
export const selfReportSteps = {
  profileClaimed: { field: "profile_claimed", options: yesNoOptions, next: "googleDescription" },
  googleDescription: { field: "has_google_description", options: yesNoOptions, next: "googlePost" },
  googlePost: { field: "last_google_post", options: recencyOptions, next: "social" },
  socialPost: { field: "last_social_post", options: recencyOptions, next: "platforms" },
} as const satisfies Record<SelfReportPhase, { field: keyof SelfReport; options: Option<string>[]; next: Phase }>;

/** The assistant's question for each phase that opens with one. */
const phasePrompts: Partial<Record<Phase, string>> = {
  name: "Bună! Cum se numește afacerea ta?",
  type: "Ce nume frumos! Ce fel de afacere ai?",
  location: "În ce oraș și cartier te găsesc clienții?",
  website: "Ai un site web?",
  maps: "Perfect. Acum hai să te găsim pe Google Maps. Lipește linkul afacerii tale sau te caut eu.",
  profileClaimed: "Ai revendicat profilul Google?",
  googleDescription: "Ai o descriere în profilul Google?",
  googlePost: "Când ai postat ultima dată pe Google?",
  social: "Ai Instagram sau TikTok? Lipește linkurile. Poți sări peste oricare.",
  socialPost: "Când ai postat ultima dată pe rețele?",
  platforms: "Ultima întrebare! Mai ești și pe alte platforme? Alege tot ce se potrivește.",
};

/** The step each phase belongs to, from 1 to 7. */
const phaseSteps: Record<Phase, number> = {
  name: 1,
  type: 2,
  typeOther: 2,
  location: 3,
  website: 4,
  websiteUrl: 4,
  maps: 5,
  candidates: 5,
  mapsError: 5,
  profileClaimed: 5,
  googleDescription: 5,
  googlePost: 5,
  social: 6,
  socialPost: 6,
  platforms: 7,
};

/** The card field names, one per step. */
export const stepNames = [
  "Nume",
  "Tip",
  "Locație",
  "Site",
  "Google Maps",
  "Rețele sociale",
  "Alte platforme",
];

/** The SVG path of the cup icon on the type field. */
const cupIcon = "M5 8h12v6a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5zM17 9h1.5a2.5 2.5 0 0 1 0 5H17M8 3v2M11 3v2M14 3v2";

/** The SVG path of the globe icon on the website field. */
const globeIcon = "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18";

/** The SVG path of the map icon on the Google Maps field. */
const mapIcon = "M9 4L3 6.5v13L9 17l6 2.5 6-2.5v-13L15 6.5 9 4zM9 4v13M15 6.5v13";

/** The SVG path of the link icon. */
export const linkIcon = "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1";

/** The SVG path of the broken link icon. */
export const linkOffIcon = `${linkIcon}M4 4l16 16`;

/** The SVG path of the warning icon. */
export const warningIcon = "M12 3l9.5 17h-19zM12 10v4M12 17.5v.01";

/** The card field icons, one per step. */
const stepIcons = [iconPath.store, cupIcon, chapterIconPath.profil, globeIcon, mapIcon, chapterIconPath.social, iconPath.grid];

/** The answers before the owner has said anything. */
export const emptyAnswers: Answers = {
  businessName: "",
  businessType: null,
  typeLabel: "",
  city: "",
  neighborhood: "",
  hasWebsite: null,
  websiteUrl: null,
  googleChoice: null,
  place: null,
  mapsUrl: null,
  selfReport: { profile_claimed: null, has_google_description: null, last_google_post: null, last_social_post: null },
  hasAnsweredSocial: false,
  instagramUrl: null,
  tiktokUrl: null,
  platforms: [],
  usesNoOtherPlatforms: false,
};

/** Returns whether a phase is one of the quick-reply self-report questions. */
export function isSelfReportPhase(phase: Phase): phase is SelfReportPhase {
  return phase in selfReportSteps;
}

/** Returns the assistant's question that opens a phase, or `null` when the phase has none. */
export function getPhasePrompt(phase: Phase): string | null {
  return phasePrompts[phase] ?? null;
}

/** Returns the step, from 1 to 7, that a phase belongs to. */
export function getStepNumber(phase: Phase): number {
  return phaseSteps[phase];
}

/** Returns the assistant's line that introduces the place candidates. */
export function getCandidatesPrompt(count: number): string {
  return count === 1
    ? "Am găsit 1 loc care se potrivește. Ești tu?"
    : `Am găsit ${count} locuri care se potrivesc. Care dintre ele ești tu?`;
}

/** Returns the business name's initials: the first letters of its first two words. */
export function getInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

/** Returns "N recenzii" with the Romanian "de" that numbers above 19 need. */
function getReviewCountLabel(count: number): string {
  if (count === 1) {
    return "1 recenzie";
  }
  const lastTwoDigits = count % 100;
  return lastTwoDigits === 0 || lastTwoDigits >= 20 ? `${count} de recenzii` : `${count} recenzii`;
}

/** Returns the line under a candidate's address: type, rating and review count. */
export function getCandidateMeta(candidate: PlaceCandidate): string {
  const parts = [candidate.type_label_ro];
  if (candidate.rating !== null) {
    parts.push(`${candidate.rating.toString().replace(".", ",")} ★`);
  }
  if (candidate.review_count !== null) {
    parts.push(getReviewCountLabel(candidate.review_count));
  }
  return parts.join(" · ");
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

/** Returns what the card shows for each step, or `null` while that step has no answer. */
function getFieldValues(answers: Answers): (string | null)[] {
  const location = [answers.neighborhood, answers.city].filter(Boolean).join(", ");
  const networks = [answers.instagramUrl ? "Instagram" : null, answers.tiktokUrl ? "TikTok" : null].filter(Boolean);
  const platforms = answers.usesNoOtherPlatforms ? ["Nu folosesc altele"] : getPlatformLabels(answers.platforms);
  const googleValues = { place: answers.place?.address ?? null, none: "Fără profil Google", later: "Îl adaug mai târziu" };
  let site: string | null = null;
  if (answers.hasWebsite !== null) {
    site = answers.hasWebsite ? answers.websiteUrl : "Fără site";
  }
  let social: string | null = null;
  if (answers.hasAnsweredSocial) {
    social = networks.length > 0 ? networks.join(", ") : "Fără rețele";
  }
  return [
    answers.businessName || null,
    answers.typeLabel || null,
    location || null,
    site,
    answers.googleChoice ? googleValues[answers.googleChoice] : null,
    social,
    platforms.length > 0 ? platforms.join(", ") : null,
  ];
}

/** Returns the business card's seven fields for the step the owner is on. */
export function getCardFields(answers: Answers, stepNumber: number): CardField[] {
  const values = getFieldValues(answers);
  const activeTexts = ["Completăm acum…", "Completăm acum…", "Completăm acum…", "Completăm acum…", "Alegem locul potrivit…", "Completăm acum…", "Alegi acum…"];
  return stepNames.map((label, index) => {
    const step = index + 1;
    const value = values[index];
    if (step < stepNumber) {
      return { label, value: value ?? "", icon: stepIcons[index], status: "done" };
    }
    if (step === stepNumber) {
      return { label, value: value ?? activeTexts[index], icon: stepIcons[index], status: "active" };
    }
    return { label, value: "Urmează", icon: stepIcons[index], status: "pending" };
  });
}

/** Returns the request that starts the scan from the owner's answers. */
export function getScanInputs(answers: Answers): ScanInputs {
  const hasNoProfile = answers.googleChoice === "none";
  const isOtherPlatformsSkipped = !answers.usesNoOtherPlatforms && answers.platforms.length === 0;
  return {
    business_name: answers.businessName,
    business_type: answers.businessType ?? "altceva",
    business_type_label_ro: answers.typeLabel,
    city: answers.city,
    neighborhood: answers.neighborhood,
    has_website: answers.hasWebsite === true,
    website_url: answers.hasWebsite ? answers.websiteUrl : null,
    place_id: answers.place?.place_id ?? null,
    maps_url: answers.mapsUrl,
    no_google_profile: hasNoProfile,
    instagram_url: answers.instagramUrl,
    tiktok_url: answers.tiktokUrl,
    platforms: isOtherPlatformsSkipped ? null : answers.platforms,
    self_report: answers.selfReport,
  };
}

/** Returns the owner's bubble that answers the platforms question. */
export function getPlatformsTurn(answers: Answers): ChatTurn {
  if (answers.usesNoOtherPlatforms) {
    return { role: "user", text: "Nu folosesc altele", kind: "text" };
  }
  if (answers.platforms.length === 0) {
    return { role: "user", text: "Sar peste", kind: "skipped" };
  }
  return { role: "user", text: getPlatformLabels(answers.platforms).join(", "), kind: "text" };
}

/** Returns the scripted conversation as contract messages, one second apart from `startedAt`. */
export function getMessages(turns: ChatTurn[], startedAt: Date): Message[] {
  return turns.map((turn, index) => ({
    id: `onboarding-${index + 1}`,
    role: turn.role,
    text: turn.text,
    created_at: new Date(startedAt.getTime() + index * 1000).toISOString(),
    action: null,
    chips: [],
  }));
}
