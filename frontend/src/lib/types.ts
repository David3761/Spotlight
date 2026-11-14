import type { components } from "@/lib/api-types";

/** The contract's schemas, generated from the backend's OpenAPI schema by `npm run gen:api`. */
type Schemas = components["schemas"];

/** The body of every error response. */
export type ApiErrorBody = Schemas["ErrorResponse"];
/** The request for `POST /api/places/search`. */
export type PlaceSearchRequest = Schemas["PlaceSearchRequest"];
/** A Google place the owner can pick. */
export type PlaceCandidate = Schemas["PlaceCandidate"];
/** The response of `POST /api/places/search`. */
export type PlaceSearchResponse = Schemas["PlaceSearchResponse"];
/** The self-reported onboarding answers. */
export type SelfReport = Schemas["SelfReport"];
/** The onboarding answers that start a scan. */
export type ScanInputs = Schemas["ScanInputs"];
/** The response of the endpoints that start a scan. */
export type ScanStarted = Schemas["ScanCreated"];
/** An event on the scan's progress stream. */
export type ScanEvent = Schemas["StepEvent"] | Schemas["CompleteEvent"] | Schemas["FailedEvent"];
/** The response of `GET /api/scans/{scan_id}`. */
export type ScanEnvelope = Schemas["ScanEnvelope"];
/** The full analysis of one business. */
export type Report = Schemas["Report"];
/** The analysed business. */
export type Business = Schemas["Business"];
/** A chapter of the report. */
export type Chapter = Schemas["Chapter"];
/** An open problem. */
export type Problem = Schemas["Problem"];
/** What a problem's fix panel shows. */
export type FixPayload = Schemas["FixPayload"];
/** A check that passes or was marked fixed. */
export type SolvedItem = Schemas["SolvedItem"];
/** A check that couldn't run. */
export type UnknownItem = Schemas["UnknownItem"];
/** The live Gemini test. */
export type GeminiBlock = Schemas["GeminiBlock"];
/** A business Gemini recommends instead of the owner's. */
export type TopCompetitor = Schemas["TopCompetitor"];
/** A group of live-test prompts. */
export type GeminiGroup = Schemas["GeminiGroup"];
/** One live-test prompt and what Gemini answered. */
export type GeminiPrompt = Schemas["GeminiPrompt"];
/** A source Gemini used for an answer. */
export type Source = Schemas["Source"];
/** The comparison with the most recommended competitors. */
export type Comparison = Schemas["Comparison"];
/** A fix suggested by the comparison. */
export type ComparisonAction = Schemas["ComparisonAction"];
/** One business in the comparison. */
export type CompareRow = Schemas["CompareRow"];
/** The scores after marking problems as fixed. */
export type ScoreUpdate = Schemas["ScoreUpdate"];
/** A generated fix text. */
export type GeneratedText = Schemas["GeneratedText"];
/** A question and answer. */
export type FaqEntry = Schemas["FaqItem"];
/** The generated info page for the business's website. */
export type InfoPage = Schemas["InfoPage"];
/** The developer instructions export. */
export type DevExport = Schemas["DevExport"];
/** A conversation in the list. */
export type ConversationSummary = Schemas["ConversationSummary"];
/** The response of `GET /api/scans/{scan_id}/conversations`. */
export type ConversationList = Schemas["ConversationList"];
/** The request for `POST /api/scans/{scan_id}/conversations`. */
export type ConversationCreate = Schemas["CreateConversationRequest"];
/** The response of `POST /api/scans/{scan_id}/conversations`. */
export type ConversationCreated = Schemas["CreateConversationResponse"];
/** A full conversation. */
export type Conversation = Schemas["Conversation"];
/** A chat message. */
export type Message = Schemas["Message"];
/** An action the assistant proposes. */
export type ProposedAction = Schemas["ProposedAction"];
/** A problem covered by a proposed action. */
export type ActionItem = Schemas["ProposedItem"];
/** A choice offered with a proposed action. */
export type ActionOption = Schemas["ActionOption"];
/** The response of `POST /api/conversations/{cid}/messages`. */
export type MessageReply = Schemas["PostMessageResponse"];
/** The response of `POST /api/conversations/{cid}/actions/{action_id}`. */
export type ActionResult = Schemas["ActionResult"];

/** A chapter of the report, in sidebar order. */
export type ChapterId = Chapter["id"];
/** A step of the analysis shown on the loading screen. */
export type StepId = Schemas["StepEvent"]["step"];
/** How a problem gets fixed. */
export type FixType = Problem["fix_type"];
/** Which fix panel opens for a problem. */
export type FixPanel = FixPayload["panel"];
/** The tone of a generated text. */
export type Tone = GeneratedText["tone"];
/** The kind of business picked in onboarding. */
export type BusinessType = ScanInputs["business_type"];
/** A listing platform the owner can say they're on. */
export type Platform = NonNullable<ScanInputs["platforms"]>[number];
/** An answer to a yes/no onboarding question. */
export type YesNoUnknown = NonNullable<SelfReport["profile_claimed"]>;
/** How recently the owner says they posted. */
export type PostRecency = NonNullable<SelfReport["last_google_post"]>;
/** The kind of a conversation with the assistant. */
export type ConversationKind = Conversation["kind"];

/** Returns whether a chapter with fixes has nothing left to fix: some of its checks could run and none is open. */
export function isChapterSolved(chapter: Chapter): boolean {
  return chapter.has_fixes && chapter.score !== null && chapter.problems.length === 0;
}
