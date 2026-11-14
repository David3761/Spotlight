# Prompt for Dev A — screens + fix & assistant backend

Paste everything below the line into Claude Code, started at the repo root.

---

You are building Dev A's half of a 24-hour hackathon project: a Romanian web app that audits how visible a local business is in Gemini and tells the owner what to fix. Another developer (Dev B) builds the data pipeline at the same time in their own Claude Code session. Your work and theirs meet only through `docs/contract.md`, so follow it exactly.

## Read first

1. `CLAUDE.md` (ground rules, file ownership).
2. `docs/architecture.md`: Team split, Design (including "Where the build differs from the design"), Frontend, LLM roles, 24-hour build plan.
3. `docs/contract.md`: all of it.
4. `docs/data-collection-algorithm.md`: §3.6 (social), §6 (problems and fixes), §4 (L8, L9).
5. `design/README.md`, then for each screen the desktop and mobile `*.dc.html` artboards listed in `docs/architecture.md` → Design.

## What you own

- `frontend/**`, root `package.json` and `package-lock.json`.
- In the backend: `app/api/fixes.py`, `app/api/chat.py` (you write them; Dev B only registers their routers), `app/fixes/**`, `app/assistant/**`, `app/llm/prompts/fix_*`, `app/llm/prompts/assistant_*`.

Everything else belongs to Dev B. Never edit it. Your backend code may import only `app.models`, `app.db`, `app.llm.client`, `app.services.resolution` and `app.cache`, with the exact names in `docs/contract.md` → "Backend-internal interfaces". If you need a Python package that isn't in `backend/pyproject.toml`, stop and tell me so I can ask Dev B.

Run `git pull --rebase` before each task and before every push. Nothing may bill: your code uses only the free-tier `GEMINI_API_KEY` (through `app.llm.client`), never the grounded key.

## How to read the artboards

Each `*.dc.html` is an exact spec, not runnable code. Copy markup structure, spacing, radii, colours and Romanian text. `<sc-for>` is a `.map`, `<sc-if>` a conditional, `<dc-import name="X" …>` a shared component with props, `{{ value }}` a binding to `renderVals()` in the script at the bottom. The `DCLogic` class is a behaviour spec: states, transitions and timings (1.5 s generating, toast 3.2 s, 1.3 s typing). Its data is mock data; real data comes from the API.

## Build order

Push after every task (`git pull --rebase` first). Check the acceptance line before moving on.

### Task 1 · Scaffold (hour 0–1)

- Delete `frontend/.gitkeep`, then create the app in `frontend/` with the latest `create-next-app`: TypeScript, App Router, `src/` directory, Tailwind, ESLint, import alias `@/*`, npm.
- Add Framer Motion, shadcn/ui (init, then only the components you use, e.g. `sheet`), and `openapi-typescript` as a dev dependency with the script `"gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts"`.
- Design tokens from `design/README.md` into `src/app/globals.css` under `@theme`: colours (accent, neutrals, the three score tiers, ring track), radii (14 / 20 / 28 / 999), font. Plus Jakarta Sans through `next/font/google` with subsets `latin` and `latin-ext`, weights 400–800. Light mode only; remove any dark-mode styles the template adds.
- `src/config.ts`: `APP_NAME = "[Nume aplicație]"`, `API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`. `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000` (git-ignored).
- `src/lib/api.ts`: a small typed `fetch` wrapper that throws an `ApiError` carrying the contract's `{ error: { code, message_ro } }`.
- Root `package.json` (repo root, not `frontend/`): dev dependency `concurrently`; scripts `"dev": "concurrently -n api,web -c blue,green \"npm:dev:api\" \"npm:dev:web\""`, `"dev:api": "cd backend && uv run uvicorn app.main:app --port 8000"`, `"dev:web": "npm --prefix frontend run dev"`.
- `/` redirects to `/start`.

Acceptance: `npm run dev:web` serves the app with the font and tokens applied.

### Task 2 · Shared components (hour 1–2)

Build from the artboards, with typed props:

- `ScoreRing` (`ScoreRing.dc.html`): props `score`, `size`, `thick`, `showMax`, `animateFrom`. Tier colour by value (< 40, 40–69, 70+), number always inside, "din 100" when `showMax`. Animates from `animateFrom` (or the previous score) over 1.1 s with cubic ease-out and a 6% scale bump at the end when the score goes up. `aria-label="Scor N din 100"`.
- `Sidebar` (`Sidebar.dc.html`): business card, Panou principal, Vizibilitate în Gemini with "X/12", Conversații, the 8 chapters with icon, open-problem count badge, "Începe de aici" marker and a check when a chapter has 0 problems. Business switcher, "Datele afacerii" and "Ajutor" are visible but not interactive. Active item from the route.
- `TabBar` (`TabBar.dc.html`): Acasă, Gemini, Capitole, Asistent.
- `AppShell`: sidebar at ≥ 1024 px, tab bar below.
- `Toast`: rises 12 px, stays about 3 s.
- `ChapterIcon`: the SVG paths from `Sidebar.dc.html`, keyed by `ChapterId`.

Acceptance: a temporary page renders each component at the sizes the artboards use. Delete it before pushing.

### Gate 1 · Contract frozen (hour 2)

When Dev B pushes the skeleton: pull, run the backend (`cd backend && uv sync && uv run uvicorn app.main:app --port 8000`), run `npm run gen:api`, commit `src/lib/api-types.ts`. From now on every type comes from that file and every screen calls the API. The stubs serve the Boema fixture, so screens show real-looking data from the start. Don't build a separate mock layer. If the skeleton is late, keep working on components with props and wire data later.

### Task 3 · Screen 1: onboarding (hour 2–5)

Artboards: `Main`, `MConfigurare`, `Eroare`. Route `/start`.

A scripted chat with the business card beside it (collapsible card on mobile). Seven steps, each answer filling a card field (done / active / pending, "X din 7 gata"):

1. Name (text).
2. Type: chips Cafenea, Restaurant, Bar, Salon, Hotel, Magazin, Altceva (Altceva opens a text input). Maps to `BusinessType` + `business_type_label_ro`.
3. City and neighbourhood.
4. Website: "Da" + URL, or "Nu".
5. Google Maps: paste a link (→ `POST /api/places/resolve-link`) or „Caută-mă pe Google” (→ `POST /api/places/search`, candidate cards with „Cel mai probabil”, „Asta sunt eu”, „Nu sunt aici · lipesc eu linkul”), or "Nu am profil Google". A `422 unreadable_link` shows the `Eroare` state („Lipesc alt link”, „Caută-mă pe Google”, „Sar peste, îl adaug mai târziu”; skipping sends `place_id: null`, `no_google_profile: false`). After a place is picked, three quick-reply questions fill `self_report`: „Ai revendicat profilul Google?” (Da / Nu / Nu știu), „Ai o descriere în profilul Google?” (Da / Nu / Nu știu), „Când ai postat ultima dată pe Google?” (Luna asta / Mai demult / Niciodată / Nu știu).
6. Social links: Facebook, Instagram, TikTok, each skippable. Then „Când ai postat ultima dată pe rețele?” with the same four answers.
7. Other platforms: chips TripAdvisor, Glovo, Wolt, Bolt Food, Booking, Booksy, „Nu folosesc altele”. CTA „Gata, analizează afacerea (N platforme)”.

On submit: `POST /api/scans` with `ScanInputs`, then `POST /api/scans/{id}/conversations` with `kind: "onboarding"`, title „Configurarea afacerii”, and the scripted transcript as `messages`, then go to `/scan/{id}/loading`. „Continui mai târziu” can be a no-op.

Acceptance: completing the flow against the stub creates a scan and lands on the loading route; the error state appears for a bad link.

### Task 4 · Loading (hour 5–6)

Artboards: `Analiza`, `MAnaliza`. Route `/scan/[id]/loading`.

Subscribe to `GET /api/scans/{id}/events` with `EventSource`. Five steps in fixed order (Google, Recenzii, Website, Rețele sociale, Gemini) with the pending and running texts from the artboard and `detail_ro` once done. Steps can finish out of order; "active" is the first step not yet done. Progress label „N din 5 pași gata”. On `complete`, desktop redirects to `/scan/{id}`, mobile shows „Vezi rezultatele”. On `failed`, show the message with „Încearcă din nou” (back to `/start`). Opening the route for a finished scan redirects.

### Task 5 · Dashboard, chapter, generic fix panel (hour 6–9)

Artboards: `Panou`, `MPanou`, `Capitol`, `MCapitol`, `CapitolGol`.

- `/scan/[id]`: greeting, overall ring, `summary_ro`, „N de probleme de rezolvat”, „Începe cu {start_here}”, the Gemini card (mini ring, „Apari în X din 12 răspunsuri”, top 3 competitors), „Următorii pași” from `next_steps` (each „Rezolvă” goes to `/scan/{id}/{chapter}?fix={check_id}`), „Ai rezolvat ceva?” → new assistant conversation, mobile chapter list. „Analizează din nou” → `POST /rescan` → the new scan's loading route. „Ultima analiză: azi” only, with no weekly-rescan text.
- `/scan/[id]/[chapter]`: ring, `intro_ro`, „+N puncte posibile”, problem cards (points, title, why, „Rezolvă”), collapsible „Rezolvate · N” from `solved`, an „Nu am putut verifica” list from `unknown`, „Dacă rezolvi tot” from `overall_gain_if_all_fixed`, „Unde se rezolvă” from `where_to_fix_ro`, „Deschide Profilul tău Google” (`business.google_maps_uri`) on `profil`. With 0 problems, show the `CapitolGol` state. `cunoaste` has no fixes: „Crește pe măsură ce rezolvi restul”.
- `FixPanel` shell: a right side panel on desktop, a bottom sheet on mobile, sliding in over 280 ms on a backdrop `rgba(15,23,42,0.32)`, opened by `?fix=`. The generic body (`panel: "steps"`) shows the title, why, `evidence_ro`, numbered `steps_ro`, the deep link button and „Am rezolvat”.
- „Am rezolvat”: update scores in local state first so rings animate, call `POST …/resolve`, then replace local state with `ScoreUpdate.report`. Toast „+{chapter_points_added} puncte · {chapter} a urcat la {chapter_score}”. Roll back with an error toast if the call fails.

### Task 6 · Fix backend + the designed panels (hour 9–12)

Backend (`app/fixes/`, `app/api/fixes.py`):

- `schemas.py`: `GeneratedText`, `InfoPage`, `DevExport` exactly as in the contract.
- `generate.py`: one Romanian prompt per `generate` check in `app/llm/prompts/fix_<check_id>.md`, with a generic fallback. Inputs come from `resolution.load_report`, `load_inputs` and `load_facts`; nothing is invented. If a fact is missing, leave it out. S05 Instagram bio: ≤ 150 characters, says what they serve, the neighbourhood and the hours. G08 Google description: ≤ 750 characters, no prices, no links. Tones: `prietenos`, `profesionist`, `scurt`; `variant` asks for a different wording. Use `text_call(tier="smart")` and cache by (scan, check, tone, variant) with `app.cache`. Return `included_ro` (which facts went in).
- `info_page.py`: build `InfoPage` from the facts, with the LLM writing only `description`, `subtitle`, `faq` answers and `message_ro`. Missing values (holiday hours, phone) go to `to_fill` and stay null. `html` is a clean standalone page with the same content, ready to upload.
- `dev_export.py`: deterministic Markdown from the report's `dev_export` problems: what's wrong, evidence, exact fix, how to verify. Include a `LocalBusiness` (or `CafeOrCoffeeShop`) JSON-LD snippet filled from the canonical profile and the exact robots.txt lines to add. `message_ro` is a short note to the web developer.
- `app/api/fixes.py`: `router = APIRouter()` with the three Fixes routes at their full contract paths.

Frontend panels:

- `panel: "generate_text"` (`Rezolva`, `MRezolva`): the generating state (skeleton, „Scriem descrierea…”) while the request runs, an editable textarea, counter „N / 150” in red above `max_chars`, tone chips, „Generează din nou” (variant + 1), „Am inclus: …”, the `where_ro` instructions, „Copiază și deschide Instagram” (copy, then open `deep_link`), „Am rezolvat”.
- `panel: "info_page"` (`FisaInfo`, `MFisaInfo`): the info page preview with `to_fill` values highlighted in yellow, „Descarcă” (downloads `html` as a file), „Trimite persoanei care îți face site-ul” with the editable `message_ro`, WhatsApp (`https://wa.me/?text=`), e-mail (`mailto:`) and „Copiază”.
- `panel: "dev_export"`: the same style as the info page panel, with a Markdown preview, „Descarcă” (`.md`) and the message.

Acceptance: against a real or stub report, the Instagram bio panel generates text in every tone; the info page downloads; the dev export downloads.

### Task 7 · Screen 5: Gemini (hour 12–14)

Artboards: `Gemini`, `MGemini`. Route `/scan/[id]/gemini`.

Ring, „Apari în X din 12 răspunsuri”, three groups with their prompts, „Apari” / „Nu apari”, „Ai apărut alături de:” / „Gemini a recomandat:” with `others`. Under every prompt, list its `sources` under a small „Surse:” label, with Maps sources attributed to „Google Maps” and every title linking to its `uri`. Google requires this attribution for Maps grounding, so it isn't optional even though the artboard doesn't show it. Comparison: a table on desktop, bars on mobile; show „10+” when `photo_count_capped`; `insights_ro`; `actions` link to the chapter with `?fix=`. „Testează din nou” → `POST /gemini-test` (takes about a minute; show „Testăm…” and „Îi punem din nou cele 12 întrebări…”), then replace the report. If `gemini.status` is `unknown`, say the test couldn't run and offer the retry.

### Gate 2 · First real scan (hour 14)

Dev B announces a real scan works. Run one through your onboarding and fix everything that renders wrong with real data on every screen (long names, nulls, unknown checks, 0 mentions, chapters with `score: null`).

### Task 8 · Screen 6: assistant (hour 14–18)

Backend (`app/assistant/`, `app/api/chat.py`):

- `schemas.py`: `ConversationSummary`, `Conversation`, `Message`, `ProposedAction`, `ActionResult` exactly as in the contract.
- `store.py`: read and write the `conversations` table through `app.db.get_session()`.
- `agent.py`: Gemini function calling via `app.llm.client.get_client()` with the smart model and four functions: `get_report()`, `propose_mark_resolved(check_ids)`, `generate_fix_text(check_id, tone)` (reuses `fixes/generate.py`), `what_next()`. The Romanian system prompt in `app/llm/prompts/assistant_system.md` makes it a friendly, brief assistant that never says something is fixed on its own. When the owner says they did something, it maps that to open `check_id`s from the report and calls `propose_mark_resolved`. The returned `ProposedAction` has options: all items („Da, marchează-le”), one option per single item („Doar descrierea”, labelled from the item), „Nu încă” (empty `check_ids`). Store the action as pending.
- Actions endpoint: a confirm calls `resolution.mark_resolved` and returns a follow-up („{chapter} a urcat de la X la Y, iar scorul general de la A la B. Cel mai rapid pas de aici e … Îl facem acum?” with chips „Da, hai” / „Mai târziu”). A decline returns the „Bine! Spune-mi oricând…” message with `score: null`. „undo” calls `resolution.unmark_resolved`. Title a new conversation from its first user message.
- `app/api/chat.py`: `router = APIRouter()` with the five Assistant routes at their full contract paths.

Frontend (`Conversatii`, `MConversatii`, `Chat`, `MChat`):

- List grouped by day (Azi, Ieri, date), client-side search, „Conversație nouă”, the „Ce poți să-i ceri” ideas (each starts a conversation with that text). The onboarding conversation shows with chapter „Configurare”.
- Chat: messages, a typing indicator while waiting, the action card with option chips, the „Am marcat ca rezolvate” card with items, points and „Anulează”, a toast, quick chips („Marchează ceva ca rezolvat”, „Ce fac acum?”, „Scrie-mi un text”). The right panel (desktop) shows the chapter ring with „+N azi”, its task list and the overall ring „de la 42 la 46 azi”; rings animate when scores change.

**Fallback:** if the assistant backend isn't working by hour 17, ship a scripted conversation for the demo café that follows the `Chat` artboard, using the real `resolve` endpoint for the confirm step.

### Task 9 · States and polish (hour 18–20)

Loading skeletons, API error toasts with retry, scans with no website or no Google profile, chapters with `score: null`, all-solved chapters, an empty conversation list. Compare every route at 390 px with its `M*` artboard. Check ring, sheet and toast motion. Gate 3 at hour 20: feature freeze, every artboard has a working route or state.

### Task 10 · Demo (hour 20–22)

Run the full demo path with `DEMO_MODE=fixture` and Wi-Fi off; fix what breaks. Write the click path for the presentation in `docs/demo.md`.

## Rules for you

- UI text in Romanian, copied from the artboards where it exists; follow "Where the build differs from the design" in `docs/architecture.md`.
- Buttons for actions, links for navigation, `aria-current` on the active nav item, visible focus.
- No dark mode, no auth, no screens for "Datele afacerii" or "Ajutor".
- Never compute scores yourself beyond the optimistic update; the server's numbers win.
- If something in Dev B's API doesn't match the contract, don't work around it in Dev B's files. Tell me what's wrong so I can ask Dev B.
