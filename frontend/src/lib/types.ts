/** A chapter of the report, in sidebar order. */
export type ChapterId = "profil" | "recenzii" | "continut" | "site" | "info" | "mentiuni" | "social" | "cunoaste";

/** A step of the analysis shown on the loading screen. */
export type StepId = "google" | "recenzii" | "website" | "retele" | "gemini";

/** How a problem gets fixed. */
export type FixType = "generate" | "owner_action" | "dev_export";

/** Which fix panel opens for a problem. */
export type FixPanel = "generate_text" | "info_page" | "steps" | "dev_export";

/** The tone of a generated text. */
export type Tone = "prietenos" | "profesionist" | "scurt";

/** The kind of business picked in onboarding. */
export type BusinessType = "cafenea" | "restaurant" | "bar" | "salon" | "hotel" | "magazin" | "altceva";

/** A listing platform the owner can say they're on. */
export type Platform = "tripadvisor" | "glovo" | "wolt" | "bolt_food" | "booking" | "booksy";

/** An answer to a yes/no onboarding question. */
export type YesNoUnknown = "da" | "nu" | "nu_stiu";

/** How recently the owner says they posted. */
export type PostRecency = "luna_asta" | "mai_demult" | "niciodata" | "nu_stiu";

/** The kind of a conversation with the assistant. */
export type ConversationKind = "onboarding" | "assistant";

/** The body of every error response. */
export interface ApiErrorBody {
  /** The machine-readable error. */
  error: {
    /** The error code, e.g. `unreadable_link`. */
    code: string;
    /** The message to show the owner. */
    message_ro: string;
  };
}

/** The request for `POST /api/places/search`. */
export interface PlaceSearchRequest {
  /** The business name the owner typed. */
  business_name: string;
  /** The city. */
  city: string;
  /** The neighbourhood. */
  neighborhood: string;
}

/** A Google place the owner can pick. */
export interface PlaceCandidate {
  /** The Google place ID. */
  place_id: string;
  /** The place's name. */
  name: string;
  /** The short address. */
  address: string;
  /** The place's type label, e.g. "Cafenea". */
  type_label_ro: string;
  /** The Google rating. */
  rating: number | null;
  /** The number of Google reviews. */
  review_count: number | null;
  /** When `true`, this is the most likely match. */
  best: boolean;
}

/** The response of `POST /api/places/search`. */
export interface PlaceSearchResponse {
  /** At most 5 candidates, best match first. */
  candidates: PlaceCandidate[];
}

/** The self-reported onboarding answers. */
export interface SelfReport {
  /** Whether the owner claimed the Google profile. */
  profile_claimed: YesNoUnknown | null;
  /** Whether the Google profile has a description. */
  has_google_description: YesNoUnknown | null;
  /** When the owner last posted on Google. */
  last_google_post: PostRecency | null;
  /** When the owner last posted on social media. */
  last_social_post: PostRecency | null;
}

/** The onboarding answers that start a scan. */
export interface ScanInputs {
  /** The business name. */
  business_name: string;
  /** The business type. */
  business_type: BusinessType;
  /** The type as the owner picked or typed it. */
  business_type_label_ro: string;
  /** The city. */
  city: string;
  /** The neighbourhood. */
  neighborhood: string;
  /** Whether the business has a website. */
  has_website: boolean;
  /** The website URL. */
  website_url: string | null;
  /** The picked Google place ID. */
  place_id: string | null;
  /** The pasted Google Maps link. */
  maps_url: string | null;
  /** When `true`, the owner said they have no Google profile. */
  no_google_profile: boolean;
  /** The Instagram profile URL. */
  instagram_url: string | null;
  /** The TikTok profile URL. */
  tiktok_url: string | null;
  /** The listing platforms; `null` when the question was skipped. */
  platforms: Platform[] | null;
  /** The self-reported answers. */
  self_report: SelfReport;
}

/** The response of the endpoints that start a scan. */
export interface ScanStarted {
  /** The new scan's ID. */
  scan_id: string;
}

/** An event on the scan's progress stream. */
export type ScanEvent =
  | { type: "step"; step: StepId; status: "running" | "done"; detail_ro: string | null }
  | { type: "complete"; scan_id: string }
  | { type: "failed"; message_ro: string };

/** The response of `GET /api/scans/{scan_id}`. */
export interface ScanEnvelope {
  /** The scan's ID. */
  scan_id: string;
  /** Where the scan is. */
  status: "running" | "complete" | "failed";
  /** The report, set when the scan is complete. */
  report: Report | null;
  /** The failure message, set when the scan failed. */
  error_ro: string | null;
}

/** The full analysis of one business. */
export interface Report {
  /** The scan's ID. */
  scan_id: string;
  /** When the analysis ran. */
  checked_at: string;
  /** The analysed business. */
  business: Business;
  /** The overall score, rounded. */
  overall: number;
  /** The overall score, unrounded. */
  overall_exact: number;
  /** The line under the overall ring. */
  summary_ro: string;
  /** The number of open problems across chapters. */
  open_problem_count: number;
  /** The top 3 open problems across chapters, by impact. */
  next_steps: Problem[];
  /** The live Gemini test. */
  gemini: GeminiBlock;
  /** The 8 chapters, in chapter order. */
  chapters: Chapter[];
  /** The comparison with the most recommended competitors. */
  comparison: Comparison;
}

/** The analysed business. */
export interface Business {
  /** The business name. */
  name: string;
  /** The name's initials, e.g. "CB". */
  initials: string;
  /** The business type. */
  type: BusinessType;
  /** The type label, e.g. "Cafenea". */
  type_label_ro: string;
  /** The city. */
  city: string;
  /** The neighbourhood. */
  neighborhood: string;
  /** The Google place ID. */
  place_id: string | null;
  /** The address. */
  address: string | null;
  /** The phone number. */
  phone: string | null;
  /** The website URL. */
  website: string | null;
  /** The Google Maps profile URL. */
  google_maps_uri: string | null;
  /** The Instagram profile URL. */
  instagram_url: string | null;
  /** The Instagram handle, without `@`. */
  instagram_handle: string | null;
  /** The TikTok profile URL. */
  tiktok_url: string | null;
}

/** A chapter of the report. */
export interface Chapter {
  /** The chapter's ID. */
  id: ChapterId;
  /** The chapter's name. */
  name_ro: string;
  /** The paragraph under the chapter title. */
  intro_ro: string;
  /** The text of the "Unde se rezolvă" box. */
  where_to_fix_ro: string | null;
  /** The chapter score; `null` when every check is unknown. */
  score: number | null;
  /** The chapter's weight in the overall score. */
  weight: number;
  /** The sum of the open problems' points. */
  possible_points: number;
  /** How much the overall score would rise if every problem were fixed. */
  overall_gain_if_all_fixed: number;
  /** When `false`, the chapter has no fixes of its own. */
  has_fixes: boolean;
  /** The open problems, by points descending. */
  problems: Problem[];
  /** The checks that pass or were marked fixed. */
  solved: SolvedItem[];
  /** The checks that couldn't run. */
  unknown: UnknownItem[];
}

/** An open problem. */
export interface Problem {
  /** The check's ID, e.g. "G08". */
  check_id: string;
  /** The chapter the problem belongs to. */
  chapter_id: ChapterId;
  /** The chapter's name. */
  chapter_name_ro: string;
  /** The problem's title. */
  title_ro: string;
  /** Why the problem matters. */
  why_ro: string;
  /** The chapter-score gain if fixed. */
  points: number;
  /** The overall-score gain if fixed. */
  impact: number;
  /** How the problem gets fixed. */
  fix_type: FixType;
  /** What the fix panel shows. */
  fix: FixPayload;
}

/** What a problem's fix panel shows. */
export interface FixPayload {
  /** The panel that opens. */
  panel: FixPanel;
  /** The numbered steps. */
  steps_ro: string[];
  /** The link to where the fix is made. */
  deep_link: string | null;
  /** The deep link's button label. */
  deep_link_label_ro: string | null;
  /** Where to paste a generated text. */
  where_ro: string | null;
  /** The maximum length of a generated text. */
  max_chars: number | null;
  /** What the analysis found. */
  evidence_ro: string | null;
}

/** A check that passes or was marked fixed. */
export interface SolvedItem {
  /** The check's ID. */
  check_id: string;
  /** The solved item's title. */
  title_ro: string;
  /** Whether the check passed or the owner marked it fixed. */
  source: "passed" | "claimed_fixed";
  /** The points gained, set for items the owner marked fixed. */
  points: number | null;
}

/** A check that couldn't run. */
export interface UnknownItem {
  /** The check's ID. */
  check_id: string;
  /** The check's title. */
  title_ro: string;
  /** Why it couldn't run. */
  reason_ro: string;
}

/** The live Gemini test. */
export interface GeminiBlock {
  /** Whether the test ran. */
  status: "complete" | "unknown";
  /** The Gemini visibility score. */
  score: number | null;
  /** The test's weight in the overall score. */
  weight: number;
  /** The number of prompts where the business appears. */
  mentioned: number;
  /** The number of prompts asked. */
  total: number;
  /** When the test last ran. */
  last_checked: string;
  /** The businesses Gemini recommends most often instead. */
  top_competitors: TopCompetitor[];
  /** The prompt groups: general, cartier, situatii. */
  groups: GeminiGroup[];
}

/** A business Gemini recommends instead of the owner's. */
export interface TopCompetitor {
  /** The competitor's name. */
  name: string;
  /** The competitor's Google place ID. */
  place_id: string | null;
  /** The number of prompts it appears in. */
  mentions: number;
}

/** A group of live-test prompts. */
export interface GeminiGroup {
  /** The group's ID. */
  id: "general" | "cartier" | "situatii";
  /** The group's name. */
  name_ro: string;
  /** The group's description. */
  desc_ro: string;
  /** The number of prompts where the business appears. */
  mentioned: number;
  /** The number of prompts in the group. */
  total: number;
  /** The group's prompts. */
  prompts: GeminiPrompt[];
}

/** One live-test prompt and what Gemini answered. */
export interface GeminiPrompt {
  /** The question asked. */
  text: string;
  /** When `true`, the business appears in at least 2 of 3 runs. */
  mentioned: boolean;
  /** The number of runs that mention the business. */
  runs_mentioned: number;
  /** The number of runs. */
  runs: number;
  /** The other businesses Gemini recommended. */
  others: string[];
  /** The start of one run's answer. */
  answer_excerpt: string;
  /** The sources Gemini used. */
  sources: Source[];
}

/** A source Gemini used for an answer. */
export interface Source {
  /** The source's title. */
  title: string;
  /** The source's URL. */
  uri: string;
  /** Whether the source is from Google Maps or the web. */
  kind: "maps" | "web";
}

/** The comparison with the most recommended competitors. */
export interface Comparison {
  /** The owner's business. */
  me: CompareRow;
  /** The 3 top competitors. */
  rivals: CompareRow[];
  /** The conclusions under the comparison. */
  insights_ro: string[];
  /** The fixes the comparison suggests. */
  actions: ComparisonAction[];
}

/** A fix suggested by the comparison. */
export interface ComparisonAction {
  /** The button label. */
  label_ro: string;
  /** The check the fix belongs to. */
  check_id: string;
  /** The chapter the check belongs to. */
  chapter_id: ChapterId;
}

/** One business in the comparison. */
export interface CompareRow {
  /** The business name. */
  name: string;
  /** The Google place ID. */
  place_id: string | null;
  /** The number of Google reviews. */
  review_count: number | null;
  /** The Google rating. */
  rating: number | null;
  /** The number of photos, capped at 10 by Google. */
  photo_count: number | null;
  /** When `true`, the photo count hit the cap. */
  photo_count_capped: boolean;
  /** Whether the hours cover all 7 days and special days. */
  hours_complete: boolean | null;
}

/** The scores after marking problems as fixed. */
export interface ScoreUpdate {
  /** The chapter that changed. */
  chapter_id: ChapterId;
  /** The chapter's new score. */
  chapter_score: number;
  /** The chapter points added. */
  chapter_points_added: number;
  /** The new overall score, rounded. */
  overall: number;
  /** The new overall score, unrounded. */
  overall_exact: number;
  /** The change in the unrounded overall score. */
  overall_delta: number;
  /** The full updated report. */
  report: Report;
}

/** A generated fix text. */
export interface GeneratedText {
  /** The check the text fixes. */
  check_id: string;
  /** The text's tone. */
  tone: Tone;
  /** The variant number. */
  variant: number;
  /** The generated text. */
  text: string;
  /** The facts the text includes. */
  included_ro: string[];
  /** The maximum length. */
  max_chars: number | null;
}

/** A question and answer. */
export interface FaqEntry {
  /** The question. */
  q: string;
  /** The answer. */
  a: string;
}

/** The generated info page for the business's website. */
export interface InfoPage {
  /** Where the page should live, e.g. "cafeneauaboema.ro/despre"; `null` when there's no website. */
  suggested_url: string | null;
  /** The page title. */
  title: string;
  /** The line under the title. */
  subtitle: string;
  /** The business description. */
  description: string;
  /** The address. */
  address: string | null;
  /** The area the business serves. */
  area_note: string | null;
  /** The opening hours as display lines. */
  hours: string[];
  /** The holiday hours; `null` when the owner has to fill them in. */
  holiday_hours: string | null;
  /** The phone number; `null` when the owner has to fill it in. */
  phone: string | null;
  /** The Instagram handle with `@`. */
  instagram: string | null;
  /** The other places the business is listed. */
  also_on: string[];
  /** The menu items or services. */
  menu: string[];
  /** The frequently asked questions. */
  faq: FaqEntry[];
  /** The fields the owner has to fill in. */
  to_fill: string[];
  /** The message to the web developer. */
  message_ro: string;
  /** The downloadable page. */
  html: string;
}

/** The developer instructions export. */
export interface DevExport {
  /** The instructions as Markdown. */
  markdown: string;
  /** The message to the web developer. */
  message_ro: string;
}

/** A conversation in the list. */
export interface ConversationSummary {
  /** The conversation's ID. */
  cid: string;
  /** The conversation's kind. */
  kind: ConversationKind;
  /** The conversation's title. */
  title: string;
  /** The chapter the conversation is about. */
  chapter_id: ChapterId | null;
  /** The chapter label, "Configurare" for onboarding. */
  chapter_name_ro: string | null;
  /** The last message's preview. */
  preview: string;
  /** The number of problems marked fixed in it. */
  solved_count: number;
  /** When the conversation last changed. */
  updated_at: string;
}

/** The response of `GET /api/scans/{scan_id}/conversations`. */
export interface ConversationList {
  /** The conversations, newest first. */
  conversations: ConversationSummary[];
}

/** The request for `POST /api/scans/{scan_id}/conversations`. */
export interface ConversationCreate {
  /** The conversation's kind. */
  kind: ConversationKind;
  /** The chapter the conversation is about. */
  chapter_id: ChapterId | null;
  /** The conversation's title. */
  title: string | null;
  /** The messages to start with. */
  messages: Message[] | null;
}

/** The response of `POST /api/scans/{scan_id}/conversations`. */
export interface ConversationCreated {
  /** The new conversation's ID. */
  cid: string;
}

/** A full conversation. */
export interface Conversation {
  /** The conversation's ID. */
  cid: string;
  /** The scan it belongs to. */
  scan_id: string;
  /** The conversation's kind. */
  kind: ConversationKind;
  /** The conversation's title. */
  title: string;
  /** The chapter the conversation is about. */
  chapter_id: ChapterId | null;
  /** The messages, oldest first. */
  messages: Message[];
}

/** A chat message. */
export interface Message {
  /** The message's ID. */
  id: string;
  /** Who wrote it. */
  role: "user" | "assistant";
  /** The message text. */
  text: string;
  /** When it was written. */
  created_at: string;
  /** The action the assistant proposes. */
  action: ProposedAction | null;
  /** The quick replies under the message. */
  chips: string[];
}

/** An action the assistant proposes. */
export interface ProposedAction {
  /** The action's ID. */
  action_id: string;
  /** The action's type. */
  type: "mark_resolved";
  /** The problems the action covers. */
  items: ActionItem[];
  /** The choices offered to the owner. */
  options: ActionOption[];
  /** Where the action is. */
  status: "pending" | "confirmed" | "declined" | "undone";
  /** The checks the owner confirmed. */
  confirmed_check_ids: string[];
}

/** A problem covered by a proposed action. */
export interface ActionItem {
  /** The check's ID. */
  check_id: string;
  /** The problem's title. */
  title_ro: string;
  /** The points it adds. */
  points: number;
}

/** A choice offered with a proposed action. */
export interface ActionOption {
  /** The option's ID. */
  id: string;
  /** The button label. */
  label_ro: string;
  /** The checks the option marks fixed; empty to decline. */
  check_ids: string[];
}

/** The response of `POST /api/conversations/{cid}/messages`. */
export interface MessageReply {
  /** The assistant's reply. */
  reply: Message;
}

/** The response of `POST /api/conversations/{cid}/actions/{action_id}`. */
export interface ActionResult {
  /** The action after the owner's choice. */
  action: ProposedAction;
  /** The new scores; `null` when declined. */
  score: ScoreUpdate | null;
  /** The assistant's follow-up. */
  followup: Message | null;
}
