# API contract (v1, frozen at gate 1)

*Final version · 14 November 2026*

The single source of truth for every request and response between the frontend and the backend. The backend implements it in Pydantic (`backend/app/models.py` for the scan side, `backend/app/fixes/schemas.py` and `backend/app/assistant/schemas.py` for the fix and assistant side). The frontend generates its types from the backend's OpenAPI schema (`npm run gen:api` → `frontend/src/lib/api-types.ts`), never by hand.

**Changing the contract:** only additive, optional fields after gate 1. The change goes into this file and the Pydantic model in the same commit, with a commit message starting `contract:`. Dev B owns this file; Dev A edits only the **Fixes** and **Assistant** sections.

Conventions:

- Base URL `http://localhost:8000` (`NEXT_PUBLIC_API_URL`). JSON everywhere, `snake_case` keys, ISO 8601 UTC timestamps.
- User-facing text fields end in `_ro` and are ready to display.
- Scores are integers 0–100. `overall_exact` keeps the unrounded value so deltas add up (42.2 + 3.6 → 46, not 42 + 3.6 → 45.6 → 46 by luck).
- Errors: HTTP status plus `{ "error": { "code": "<code>", "message_ro": "<text>" } }`. Codes: `unreadable_link` (422), `place_not_found` (404), `scan_not_found` (404), `scan_running` (409), `check_not_found` (404), `upstream_error` (502).

---

## Shared types

```ts
type ChapterId = "profil" | "recenzii" | "continut" | "site" | "info" | "mentiuni" | "social" | "cunoaste";
type StepId = "google" | "recenzii" | "website" | "retele" | "gemini";
type CheckStatus = "pass" | "partial" | "fail" | "unknown";
type FixType = "generate" | "owner_action" | "dev_export";
type FixPanel = "generate_text" | "info_page" | "steps" | "dev_export";
type Tone = "prietenos" | "profesionist" | "scurt";
type BusinessType = "cafenea" | "restaurant" | "bar" | "salon" | "hotel" | "magazin" | "altceva";
type Platform = "tripadvisor" | "glovo" | "wolt" | "bolt_food" | "booking" | "booksy";
type YesNoUnknown = "da" | "nu" | "nu_stiu";
type PostRecency = "luna_asta" | "mai_demult" | "niciodata" | "nu_stiu";
```

Chapter order (sidebar, dashboard, `chapters[]`): `profil`, `recenzii`, `continut`, `site`, `info`, `mentiuni`, `social`, `cunoaste`. Gemini visibility is not a chapter: it has its own `gemini` block and the `/scan/[id]/gemini` route.

---

## Onboarding and places (owner: Dev B)

### `POST /api/places/search`

Request:

```ts
interface PlaceSearchRequest { business_name: string; city: string; neighborhood: string; }
```

Response:

```ts
interface PlaceSearchResponse { candidates: PlaceCandidate[]; }   // at most 5, best match first

interface PlaceCandidate {
  place_id: string;
  name: string;
  address: string;            // short, e.g. "Str. Dr. Lister, Cotroceni"
  type_label_ro: string;      // "Cafenea"
  rating: number | null;      // 4.6
  review_count: number | null;
  best: boolean;              // true on the first candidate when its name matches ("Cel mai probabil")
}
```

### `POST /api/places/resolve-link`

Request `{ "url": string }` (a `maps.app.goo.gl/…` or full Google Maps link). Response `PlaceCandidate`, or `422 unreadable_link` (the `Eroare` state).

---

## Scans (owner: Dev B)

### `POST /api/scans`

Request:

```ts
interface ScanInputs {
  business_name: string;
  business_type: BusinessType;
  business_type_label_ro: string;       // what the owner picked or typed, e.g. "Cafenea"
  city: string;
  neighborhood: string;
  has_website: boolean;
  website_url: string | null;
  place_id: string | null;              // from search or resolve-link
  maps_url: string | null;
  no_google_profile: boolean;           // owner said "nu am profil Google"
  instagram_url: string | null;
  tiktok_url: string | null;
  platforms: Platform[] | null;         // null = question skipped, [] = "Nu folosesc altele"
  self_report: SelfReport;
}

interface SelfReport {
  profile_claimed: YesNoUnknown | null;         // G12
  has_google_description: YesNoUnknown | null;  // G08
  last_google_post: PostRecency | null;         // G09
  last_social_post: PostRecency | null;         // S03 fallback when Instagram can't be read
}
```

Response `{ "scan_id": string }`. The analysis starts immediately.

### `GET /api/scans/{scan_id}/events` (SSE)

`text/event-stream`, one JSON object per `data:` line:

```ts
type ScanEvent =
  | { type: "step"; step: StepId; status: "running" | "done"; detail_ro: string | null }
  | { type: "complete"; scan_id: string }
  | { type: "failed"; message_ro: string };
```

- `detail_ro` is set on `done`, e.g. `"Am găsit Profilul tău Google"`, `"Am găsit 38 de recenzii"`, `"Am citit cafeneauaboema.ro"`, `"Am verificat Instagram"`, `"I-am pus lui Gemini 12 întrebări"`.
- Steps can finish in any order; the frontend marks each one independently.
- Connecting after the scan finished replays every `done` event, then `complete`.

### `GET /api/scans/{scan_id}`

```ts
interface ScanEnvelope {
  scan_id: string;
  status: "running" | "complete" | "failed";
  report: Report | null;          // set when status = "complete"
  error_ro: string | null;
}
```

### `POST /api/scans/{scan_id}/rescan`

„Analizează din nou”: starts a new scan with the same inputs. Response `{ "scan_id": string }` (the new one).

### `POST /api/scans/{scan_id}/problems/{check_id}/resolve`

„Am rezolvat”: marks the problem as claimed fixed and adds its points provisionally. Response `ScoreUpdate`.

### `POST /api/scans/{scan_id}/gemini-test`

„Testează din nou”: reruns only the live Gemini test (blocking, about 60 s). Response: the updated `Report`.

---

## Report

```ts
interface Report {
  scan_id: string;
  checked_at: string;
  business: Business;
  overall: number;                  // rounded, shown in the ring
  overall_exact: number;            // unrounded
  summary_ro: string;               // line under the ring, e.g. "Gemini te recomandă rar deocamdată. Multe se rezolvă în câteva minute."
  open_problem_count: number;       // "30 de probleme de rezolvat"
  next_steps: Problem[];            // top 3 open problems across chapters, by impact
  gemini: GeminiBlock;
  chapters: Chapter[];              // always 8, in chapter order
  comparison: Comparison;           // Screen 5 "De ce îi alege Gemini pe ei?"
}

interface Business {
  name: string;
  initials: string;                 // "CB"
  type: BusinessType;
  type_label_ro: string;            // "Cafenea"
  city: string;
  neighborhood: string;
  place_id: string | null;
  address: string | null;
  phone: string | null;
  website: string | null;
  google_maps_uri: string | null;   // "Deschide Profilul tău Google"
  instagram_url: string | null;
  instagram_handle: string | null;  // "cafeneauaboema", no @
  tiktok_url: string | null;
}

interface Chapter {
  id: ChapterId;
  name_ro: string;                  // "Profilul Google"
  intro_ro: string;                 // paragraph under the title on the chapter page
  where_to_fix_ro: string | null;   // "Unde se rezolvă" box
  score: number | null;             // null when every check is unknown
  weight: number;                   // 0.20 … 0.05
  possible_points: number;          // Σ open problem points ("+35 puncte posibile")
  overall_gain_if_all_fixed: number;// "Scorul general ar crește cu aproximativ 7 puncte"
  has_fixes: boolean;               // false for "cunoaste" → "Crește pe măsură ce rezolvi restul"
  problems: Problem[];              // open only, by points descending
  solved: SolvedItem[];             // "Rezolvate · N"
  unknown: UnknownItem[];           // "Nu am putut verifica"
}

interface Problem {
  check_id: string;                 // "G08", or "L02:glovo:phone" for per-field mismatches
  chapter_id: ChapterId;
  chapter_name_ro: string;
  title_ro: string;                 // "Fără descriere a afacerii"
  why_ro: string;
  points: number;                   // chapter-score gain if fixed ("+10")
  impact: number;                   // points × chapter weight, in overall points (float)
  fix_type: FixType;
  fix: FixPayload;
}

interface FixPayload {
  panel: FixPanel;                  // which side panel opens
  steps_ro: string[];               // numbered steps; for generate_text, where to paste it
  deep_link: string | null;         // Google Maps profile, Instagram profile, …
  deep_link_label_ro: string | null;// "Copiază și deschide Instagram"
  where_ro: string | null;          // "Profil › Editează profilul › Biografie"
  max_chars: number | null;         // 150 for the Instagram bio
  evidence_ro: string | null;       // what we found, e.g. "Am găsit 2 fotografii"
}

interface SolvedItem {
  check_id: string;
  title_ro: string;                 // passed: "Numărul de telefon e afișat"; claimed: the problem title
  source: "passed" | "claimed_fixed";
  points: number | null;            // set for claimed_fixed ("+6")
}

interface UnknownItem { check_id: string; title_ro: string; reason_ro: string; }

interface GeminiBlock {
  status: "complete" | "unknown";   // unknown when the live test failed
  score: number | null;
  weight: number;                   // 0.10
  mentioned: number;                // 2
  total: number;                    // 12
  last_checked: string;
  top_competitors: { name: string; place_id: string | null; mentions: number }[];  // top 3, "în 9 răspunsuri"
  groups: GeminiGroup[];            // general, cartier, situatii
}

interface GeminiGroup {
  id: "general" | "cartier" | "situatii";
  name_ro: string;                  // "General"
  desc_ro: string;                  // "Întrebări despre tot orașul"
  mentioned: number;
  total: number;
  prompts: GeminiPrompt[];
}

interface GeminiPrompt {
  text: string;                     // "cafenea în Cotroceni"
  mentioned: boolean;               // in at least 2 of 3 runs
  runs_mentioned: number;
  runs: number;
  others: string[];                 // other businesses Gemini recommended
  answer_excerpt: string;           // first ~300 chars of one run's answer
  sources: Source[];                // shown under the prompt, with Google Maps attribution
}

interface Source { title: string; uri: string; kind: "maps" | "web"; }

interface Comparison {
  me: CompareRow;
  rivals: CompareRow[];             // the 3 top competitors from the live test
  insights_ro: string[];            // ["Ai o notă la fel de bună ca ei.", "Îți lipsesc recenziile, fotografiile și programul complet, …"]
  actions: { label_ro: string; check_id: string; chapter_id: ChapterId }[];  // "Strânge mai multe recenzii" → R01
}

interface CompareRow {
  name: string;
  place_id: string | null;
  review_count: number | null;
  rating: number | null;
  photo_count: number | null;       // Places caps at 10
  photo_count_capped: boolean;      // true → show "10+"
  hours_complete: boolean | null;   // 7 days + special hours
}

interface ScoreUpdate {
  chapter_id: ChapterId;
  chapter_score: number;
  chapter_points_added: number;     // "+6 puncte"
  overall: number;
  overall_exact: number;
  overall_delta: number;            // overall_exact after − before
  report: Report;                   // the full updated report, for reconciling local state
}
```

---

## Fixes (owner: Dev A)

### `POST /api/scans/{scan_id}/fixes/{check_id}/generate`

Request `{ "tone": Tone, "variant": number }` (`variant` increments on „Generează din nou”). Response:

```ts
interface GeneratedText {
  check_id: string;
  tone: Tone;
  variant: number;
  text: string;
  included_ro: string[];            // ["cartierul", "ce servești", "programul"] → "Am inclus: …"
  max_chars: number | null;
}
```

Works for every problem with `fix_type = "generate"`; the Instagram bio (`S05`) and the Google description (`G08`) are the ones the demo shows.

### `GET /api/scans/{scan_id}/info-page`

```ts
interface InfoPage {
  suggested_url: string | null;     // "cafeneauaboema.ro/despre"; null when there's no website
  title: string;                    // "Cafeneaua Boema"
  subtitle: string;                 // "Cafenea de specialitate în Cotroceni, București"
  description: string;
  address: string | null;
  area_note: string | null;         // "Servim clienți din Cotroceni și din cartierele din jur"
  hours: string[];                  // ["Luni–Duminică: 8:00–20:00"]
  holiday_hours: string | null;     // null → shown as "de completat"
  phone: string | null;             // null → shown as "numărul tău"
  instagram: string | null;         // "@cafeneauaboema"
  also_on: string[];                // ["Google Maps", "Glovo", "Wolt"]
  menu: string[];
  faq: { q: string; a: string }[];
  to_fill: string[];                // field names highlighted in yellow
  message_ro: string;               // pre-written message to the web developer
  html: string;                     // downloadable page ("Descarcă")
}
```

### `GET /api/scans/{scan_id}/dev-export`

```ts
interface DevExport { markdown: string; message_ro: string; }
```

One Markdown document with every `dev_export` problem: what's wrong, evidence, exact fix (robots.txt lines, filled JSON-LD snippet, …), how to verify.

---

## Assistant (owner: Dev A)

An unknown `cid`, `action_id` or `option_id` returns `404 conversation_not_found`. After „Anulează” (status `undone`) the action's options can be answered again.

### `GET /api/scans/{scan_id}/conversations`

```ts
interface ConversationSummary {
  cid: string;
  kind: "onboarding" | "assistant";
  title: string;
  chapter_id: ChapterId | null;
  chapter_name_ro: string | null;   // "Configurare" for onboarding
  preview: string;                  // "Asistent: Gata! Am marcat 2 probleme…"
  solved_count: number;             // "2 rezolvate"
  updated_at: string;
}
```

Response `{ "conversations": ConversationSummary[] }`, newest first.

### `POST /api/scans/{scan_id}/conversations`

Request `{ "kind": "onboarding" | "assistant", "chapter_id": ChapterId | null, "title": string | null, "messages": Message[] | null }`. The frontend creates the onboarding conversation once, right after `POST /api/scans`, with the scripted transcript in `messages`. Response `{ "cid": string }`.

### `GET /api/conversations/{cid}`

```ts
interface Conversation {
  cid: string;
  scan_id: string;
  kind: "onboarding" | "assistant";
  title: string;
  chapter_id: ChapterId | null;
  messages: Message[];
}

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  created_at: string;
  action: ProposedAction | null;
  chips: string[];                  // quick replies under the message ("Da, hai", "Mai târziu")
}

interface ProposedAction {
  action_id: string;
  type: "mark_resolved";
  items: { check_id: string; title_ro: string; points: number }[];
  options: { id: string; label_ro: string; check_ids: string[] }[];  // "Da, marchează-le" / "Doar descrierea" / "Nu încă" (empty check_ids)
  status: "pending" | "confirmed" | "declined" | "undone";
  confirmed_check_ids: string[];
}
```

### `POST /api/conversations/{cid}/messages`

Request `{ "text": string }`. Response `{ "reply": Message }` (not streamed; the frontend shows a typing indicator while waiting). The reply may carry a `ProposedAction`; nothing changes until the owner picks an option.

### `POST /api/conversations/{cid}/actions/{action_id}`

Request `{ "option_id": string }` to confirm or decline, or `{ "option_id": "undo" }` for „Anulează”. Response:

```ts
interface ActionResult {
  action: ProposedAction;
  score: ScoreUpdate | null;        // null when declined
  followup: Message | null;         // "Profilul Google a urcat de la 65 la 83, …"
}
```

---

## Backend-internal interfaces both devs use

These are Python, not HTTP. Dev B owns and implements them, and they must exist with these exact names at gate 1, because Dev A's fix and assistant endpoints import them. Every function raises `ScanNotFound` (defined in `app/services/resolution.py`) for an unknown `scan_id`.

```python
# app/models.py (in addition to the HTTP models above)
class WebsiteFacts(BaseModel):
    what_it_is: str | None                 # "cafenea de specialitate cu boabe prăjite local"
    menu_items_or_services: list[str]      # ["Espresso", "Flat white", ...]
    prices_present: bool
    faq_items: list[FaqItem]               # questions the site already answers
    language: str | None                   # "ro", "en", ...

class FaqItem(BaseModel):
    q: str
    a: str

class Facts(BaseModel):                    # what fix texts and the info page are written from
    name: str
    type_label_ro: str                     # "Cafenea"
    city: str
    neighborhood: str
    address: str | None                    # Google's formatted address
    phone: str | None                      # national format, e.g. "0721 234 567"
    website: str | None
    google_maps_uri: str | None
    hours_ro: list[str]                    # ["Luni–Duminică: 8:00–20:00"]; [] when unknown
    special_hours_ro: list[str]            # upcoming special days as display lines; [] when none
    attributes_ro: list[str]               # true attributes as labels: ["Terasă", "Plata cu cardul", "Câini acceptați"]
    instagram_handle: str | None           # no @
    tiktok_url: str | None
    platforms_ro: list[str]                # where else it's listed: ["Glovo", "Wolt"]
    website_facts: WebsiteFacts | None     # None when there's no website or it couldn't be read

# app/services/resolution.py
class ScanNotFound(Exception): ...
def mark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate: ...
def unmark_resolved(scan_id: str, check_ids: list[str]) -> ScoreUpdate: ...
def load_report(scan_id: str) -> Report: ...
def load_inputs(scan_id: str) -> ScanInputs: ...
def load_facts(scan_id: str) -> Facts: ...

# app/llm/client.py   (free-tier GEMINI_API_KEY; grounded calls are Dev B's only)
Tier = Literal["fast", "smart"]
async def json_call(prompt: str, schema: type[T], tier: Tier = "fast", system: str | None = None) -> T: ...
async def text_call(prompt: str, tier: Tier = "smart", system: str | None = None, run: int = 0) -> str: ...  # run: repeated asks cached apart
def get_client() -> genai.Client: ...      # for function calling in the assistant
def get_model(tier: Tier) -> str: ...      # the model ID for a tier, from .env

# app/cache.py   (JSON files under backend/cache/, keyed by SHA-256 of the joined parts)
def get(parts: list[str]) -> Any | None: ...
def set(parts: list[str], value: Any) -> None: ...

# app/db.py
class ConversationRow(SQLModel, table=True):
    __tablename__ = "conversations"
    id: str = Field(primary_key=True)
    scan_id: str = Field(index=True)
    kind: str                              # "onboarding" | "assistant"
    title: str
    chapter_id: str | None = None
    messages: str = "[]"                   # JSON text: list[Message]
    pending_actions: str = "[]"            # JSON text: list[ProposedAction]
    created_at: datetime
    updated_at: datetime

def get_session() -> Session: ...          # a new SQLModel Session; use as `with get_session() as session:`
```

`main.py` (Dev B) registers Dev A's routers with `from app.api import chat, fixes`, then `app.include_router(fixes.router)` and `app.include_router(chat.router)`, no prefix: each router declares the full paths from this contract. Dev B also creates the empty package files `app/__init__.py` and `app/api/__init__.py`.
