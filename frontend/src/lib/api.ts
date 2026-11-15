import { API_URL } from "@/config";
import type {
  ActionResult,
  ApiErrorBody,
  Conversation,
  ConversationCreate,
  ConversationCreated,
  ConversationList,
  DevExport,
  GeneratedText,
  InfoPage,
  MessageReply,
  OnboardingTurn,
  OnboardingTurnRequest,
  Report,
  ReviewAlerts,
  ReviewAlertSent,
  ScanEnvelope,
  ScanEvent,
  ScanInputs,
  ScanStarted,
  ScoreUpdate,
  Tone,
} from "@/lib/types";

/** A failed request: an error response from the backend, or no response at all. */
export class ApiError extends Error {
  /** The contract's error code, or `network` when the server couldn't be reached. */
  readonly code: string;
  /** The HTTP status, or `null` when there was no response. */
  readonly status: number | null;
  /** The backend's message for the owner, when it sent one. */
  readonly messageRo: string | null;

  /** Creates an {@link ApiError}. */
  constructor(code: string, status: number | null, messageRo: string | null) {
    super(messageRo ?? code);
    this.code = code;
    this.status = status;
    this.messageRo = messageRo;
  }
}

/** Sends a request to the backend and returns the parsed JSON body. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    });
  } catch {
    throw new ApiError("network", null, null);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(body?.error?.code ?? "http_error", response.status, body?.error?.message_ro ?? null);
  }
  return (await response.json()) as T;
}

/** Sends a JSON body with `POST`. */
function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}

/** Returns the onboarding assistant's reply to the owner's newest message, with the answers collected so far. */
export function sendOnboardingMessage(turn: OnboardingTurnRequest): Promise<OnboardingTurn> {
  return post("/api/onboarding/turn", turn);
}

/** Starts a scan from the onboarding answers. */
export function startScan(inputs: ScanInputs): Promise<ScanStarted> {
  return post("/api/scans", inputs);
}

/** Returns a scan's status and, once complete, its report. */
export function getScan(scanId: string): Promise<ScanEnvelope> {
  return request(`/api/scans/${scanId}`);
}

/** Starts a new scan with the same inputs as an earlier one. */
export function rescan(scanId: string): Promise<ScanStarted> {
  return post(`/api/scans/${scanId}/rescan`);
}

/** Marks a problem as fixed and returns the new scores. */
export function resolveProblem(scanId: string, checkId: string): Promise<ScoreUpdate> {
  return post(`/api/scans/${scanId}/problems/${checkId}/resolve`);
}

/** Reruns the live Gemini test and returns the updated report. */
export function runGeminiTest(scanId: string): Promise<Report> {
  return post(`/api/scans/${scanId}/gemini-test`);
}

/** Generates a fix text in the given tone. */
export function generateFixText(scanId: string, checkId: string, tone: Tone, variant: number): Promise<GeneratedText> {
  return post(`/api/scans/${scanId}/fixes/${checkId}/generate`, { tone, variant });
}

/** Returns the info page prepared for the business's website. */
export function getInfoPage(scanId: string): Promise<InfoPage> {
  return request(`/api/scans/${scanId}/info-page`);
}

/** Returns the instructions for the web developer. */
export function getDevExport(scanId: string): Promise<DevExport> {
  return request(`/api/scans/${scanId}/dev-export`);
}

/** Returns the scan's WhatsApp review alerts. */
export function getReviewAlerts(scanId: string): Promise<ReviewAlerts> {
  return request(`/api/scans/${scanId}/review-alerts`);
}

/** Turns on WhatsApp review alerts for the owner's phone number. */
export function enableReviewAlerts(scanId: string, phone: string): Promise<ReviewAlerts> {
  return request(`/api/scans/${scanId}/review-alerts`, { method: "PUT", body: JSON.stringify({ phone }) });
}

/** Turns off the scan's WhatsApp review alerts. */
export function disableReviewAlerts(scanId: string): Promise<ReviewAlerts> {
  return request(`/api/scans/${scanId}/review-alerts`, { method: "DELETE" });
}

/** Sends the WhatsApp alert for the newest review now, as if it had just arrived. */
export function simulateReviewAlert(scanId: string): Promise<ReviewAlertSent> {
  return post(`/api/scans/${scanId}/review-alerts/simulate`);
}

/** Returns a scan's conversations, newest first. */
export function getConversations(scanId: string): Promise<ConversationList> {
  return request(`/api/scans/${scanId}/conversations`);
}

/** Creates a conversation for a scan. */
export function createConversation(scanId: string, conversation: ConversationCreate): Promise<ConversationCreated> {
  return post(`/api/scans/${scanId}/conversations`, conversation);
}

/** Returns a conversation with all its messages. */
export function getConversation(cid: string): Promise<Conversation> {
  return request(`/api/conversations/${cid}`);
}

/** Sends the owner's message and returns the assistant's reply. */
export function sendMessage(cid: string, text: string): Promise<MessageReply> {
  return post(`/api/conversations/${cid}/messages`, { text });
}

/** Confirms, declines or undoes a proposed action. */
export function answerAction(cid: string, actionId: string, optionId: string): Promise<ActionResult> {
  return post(`/api/conversations/${cid}/actions/${actionId}`, { option_id: optionId });
}

/** Subscribes to a scan's progress stream and returns a function that closes it. */
export function subscribeToScanEvents(
  scanId: string,
  onEvent: (event: ScanEvent) => void,
  onConnectionError: () => void,
): () => void {
  const source = new EventSource(`${API_URL}/api/scans/${scanId}/events`);
  source.onmessage = (message) => onEvent(JSON.parse(message.data) as ScanEvent);
  source.onerror = onConnectionError;
  return () => source.close();
}
