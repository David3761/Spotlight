# Prompt for Dev B — data pipeline

Paste everything below the line into Claude Code, started at the repo root.

---

You are building Dev B's half of a 24-hour hackathon project: a Romanian web app that audits how visible a local business is in Gemini and tells the owner what to fix. You build the FastAPI backend and the whole analysis pipeline. Another developer (Dev A) builds the screens plus the backend for fix texts and the assistant chat, at the same time in their own Claude Code session. Your work and theirs meet through `docs/contract.md`, so follow it exactly.

## Step 0

Run `git pull --rebase` now, before reading anything: Dev A has already pushed code and keeps pushing. Then follow `CLAUDE.md` → "How to work": ask all your questions together before writing code, and keep later questions for the end.

## Read first

1. `CLAUDE.md` (how to work, development rules, file ownership).
2. `docs/architecture.md`: all of it.
3. `docs/contract.md`: all of it. You own this file and `app/models.py`.
4. `docs/data-collection-algorithm.md`: all of it. This is your spec for every check, source, point value and timeout.
5. `design/README.md`, plus `design/Panou.dc.html`, `Capitol.dc.html`, `Rezolva.dc.html`, `FisaInfo.dc.html`, `Gemini.dc.html`, `Analiza.dc.html` for the fixture's mock data, problem titles and progress texts.

## What you own

Everything in `backend/**` except Dev A's paths: `app/api/fixes.py`, `app/api/chat.py`, `app/fixes/**`, `app/assistant/**`, `app/llm/prompts/fix_*`, `app/llm/prompts/assistant_*`. Dev A has already written those against the contract; you never create or edit them, you only register the two routers in `main.py`. Never edit anything in `frontend/` or the root `package.json`.

Dev A's backend code imports only `app.models`, `app.db`, `app.llm.client`, `app.services.resolution` and `app.cache`, with the exact names in `docs/contract.md` → "Backend-internal interfaces". Keep them stable once pushed: add, don't rename.

## Working alongside Dev A

- Dev A pushes to `main` often. Run `git pull --rebase` before you start and before each task, and again before every push. Never force-push.
- Run anything that doesn't bill: local servers, tests, free API quotas, cached responses. Before calling a paid service, check its free monthly quota and stay inside it; cache every response so repeats cost nothing. Never upgrade a plan.
- The one key that bills is `GEMINI_GROUNDED_API_KEY` (grounded Gemini calls bill their tokens). Use it only in the live test and mentions, and only for the real scans needed for gate 2 and the demo recording. Everything else uses the free-tier `GEMINI_API_KEY`.

## Before coding (I do these by hand; remind me if a key is missing)

- Google Cloud project with billing (needed to enable the APIs; stay inside the free monthly quota): enable Places API (New) and PageSpeed Insights API, one key restricted to those two.
- SerpApi account and key (free plan).
- Two Gemini keys from AI Studio: `GEMINI_API_KEY` from a project with no billing (free tier) and `GEMINI_GROUNDED_API_KEY` from a project with billing (grounding needs the paid tier). Share both with Dev A privately.
- `cp backend/.env.example backend/.env`, then paste the keys. `META_ACCESS_TOKEN`, `META_IG_USER_ID` and `DEMO_PLACE_ID` come from Dev A; the model IDs are already filled in.
- `uv` (`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows); uv downloads Python 3.12 itself.

## Build order

Push after every task (`git pull --rebase` first). Check the acceptance line before moving on. Keep tests light: pytest for normalization, scoring and fixture validation only.

### Task 1 · Skeleton and stubs → gate 1 (hour 0–2)

- Delete `backend/.gitkeep`. `uv init` a Python 3.12 project in `backend/`. Dependencies: `fastapi`, `uvicorn[standard]`, `sse-starlette`, `sqlmodel`, `pydantic-settings`, `httpx`, `selectolax`, `playwright`, `google-genai`, `phonenumbers`, `rapidfuzz`, `tenacity`, and `pytest` as a dev dependency.
- Create the empty package files `app/__init__.py` and `app/api/__init__.py` (Dev A's packages `app/fixes/` and `app/assistant/` already exist).
- `app/config.py`: settings loaded from `backend/.env`. `backend/.env.example` already exists with every name; add a name there only if you need a new setting, with no comments.
- `app/models.py`: every scan-side Pydantic model in `docs/contract.md` (`PlaceSearchRequest`, `PlaceCandidate`, `ScanInputs`, `SelfReport`, `ScanEvent` variants, `ScanEnvelope`, `Report` and all nested types, `ScoreUpdate`), plus `Facts`, `WebsiteFacts` and `FaqItem` from "Backend-internal interfaces", with the exact field names and `Literal` types.
- `app/db.py`: SQLModel engine on `backend/app.db`; `scans` table (`id`, `created_at`, `status`, `inputs`, `internal`, `report`, `error`, JSON columns as text); `ConversationRow` and `get_session()` exactly as in the contract; `create_all` on startup.
- `app/cache.py`: `get(parts)` / `set(parts, value)` exactly as in the contract.
- `app/llm/client.py`, first version: `json_call`, `text_call`, `get_client`, `get_model` exactly as in the contract, on the free-tier `GEMINI_API_KEY`, with the model IDs from `.env`. Dev A's endpoints call them from gate 1.
- `app/services/resolution.py`: `ScanNotFound` and all five functions exactly as in the contract, working on fixture-backed scans. For those, `load_facts` returns `fixtures/boema_facts.json`, a `Facts` for Cafeneaua Boema taken from `FisaInfo.dc.html` (address, hours, Instagram, "Ne găsești și pe" without Facebook, menu, FAQ); phone and special hours stay empty, as the artboard shows them as "de completat".
- `fixtures/boema_report.json`: a complete `Report` for Cafeneaua Boema built from the design's mock data:
  - overall 42 with `overall_exact` 42.2
  - chapter scores 65 / 50 / 35 / 50 / 35 / 25 / 55 / 20 in chapter order
  - open-problem counts 5 / 3 / 6 / 4 / 5 / 4 / 3 / 0 (30 in total), `start_here: "continut"`
  - `next_steps` = the three in `Panou.dc.html`
  - Gemini score 17 with 2 of 12 mentions, groups, prompts, competitors and the comparison exactly as in `Gemini.dc.html` (photo counts above 10 → 10 with `photo_count_capped: true`), each prompt with one or two plausible sources
  - problems use catalog `check_id`s and their points; titles and reasons come from the artboards where they exist (`Capitol` for `profil`, `Rezolva` for `social` with `S05` as the Instagram bio, `FisaInfo` for `site` with `T09` as the info page)
  - no Facebook anywhere (it's dropped from the product): the three `social` problems are S05 (Instagram bio), S04 (Instagram doesn't link to the site) and S03 (no recent post); follow `docs/architecture.md` → "Where the build differs from the design" for the changed copy
  - `solved` items as in `Capitol.dc.html`
- Stub routes for every scan-side endpoint in the contract (not the Fixes and Assistant ones: those are Dev A's routers, which you register), all returning contract-shaped data built from the fixture:
  - `POST /api/scans` returns a new ID backed by the fixture.
  - SSE replays the five steps over about 8 s with the `detail_ro` texts from `Analiza.dc.html` (use „Am găsit 38 de recenzii”).
  - `resolve` moves the problem to `solved` and recomputes the numbers.
- `app/main.py`: CORS for `FRONTEND_ORIGIN`, your routers plus Dev A's (`from app.api import chat, fixes`; `app.include_router(fixes.router)`, `app.include_router(chat.router)`), the error format from the contract (map `ScanNotFound` to `404 scan_not_found`).
- Tests: the fixture validates against `Report`, `boema_facts.json` validates against `Facts`.

Push, then tell me "gate 1 ready" so I can tell Dev A. Acceptance: `uv run uvicorn app.main:app --port 8000` serves `/docs`, every endpoint (Dev A's included) answers with contract-shaped data, and pytest passes.

### Task 2 · Foundations (hour 2–5)

- `app/llm/client.py`, complete:
  - All calls go through one `asyncio.Semaphore(6)` and `tenacity` exponential backoff (3 tries), and are cached with `app.cache`.
  - `grounded_call(question, lat, lng, tools=("maps", "search"))` on `GEMINI_GROUNDED_API_KEY` with `GEMINI_MODEL_LIVE`. It sends only the question with the location and no system prompt, and returns the text plus parsed grounding chunks (maps: place ID, title, URI; web: title, URI).
  - First check how to send it. Google's Maps grounding page (14 November 2026) says Maps grounding "currently only supports English language prompts and responses", and its examples use the Interactions API (`client.interactions.create`, tool `{"type": "google_maps", "latitude", "longitude"}`) rather than `generateContent` with `toolConfig.retrievalConfig`. Read the installed `google-genai` source for what it supports, then make one real Romanian call (`"cafenea în Cotroceni"`) and check that Maps chunks come back. If they don't, stop and tell me before changing the approach.
- `app/pipeline/normalize.py`: the §4 rules (address, phone via `phonenumbers`, hours, name via `rapidfuzz`), with tests including "Str." vs "Strada" and the three phone formats.
- Places: real `POST /api/places/search` and `POST /api/places/resolve-link` (§3 step 1), and `canonical.py` (Place Details with the step 2 field mask → `CanonicalProfile`).
- `collectors/google_profile.py`: G01–G12.
- `app/pipeline/scoring.py`:
  - one catalog dict (check ID → chapter, points, fix type) and the weights
  - chapter score over known checks, with `claimed_fixed` counted as earned
  - the gates and `overall_exact` with renormalization
  - problem points and impact as in §6
  - Test: the design's mock scores give 42.2.
- `app/pipeline/problems.py`: a Romanian template for every check:
  - `title_ro`, `why_ro`, `steps_ro`, and a solved title
  - the `FixPayload` panel mapping and deep links: `google_maps_uri` for profile fixes, `https://instagram.com/{handle}` for social
  - `chapter intro_ro` and `where_to_fix_ro`
  - Copy from the artboards where they exist; the rest in the same plain, jargon-free Romanian. Templates take evidence ("Doar {n} fotografii, recomandat minim 5", "{x} din ultimele {y} recenzii fără răspuns").
- `app/services/resolution.py`, real: `mark_resolved` and `unmark_resolved` recompute scores and problems from `internal` and rewrite `report`; `load_facts` builds `Facts` from the canonical profile, the inputs and the website facts. The `resolve` endpoint becomes real and uses it.

Push, then tell me "resolve is real" (Dev A needs it by hour 6).

### Task 3 · Real pipeline and progress (hour 5–6)

`app/jobs.py`: an in-memory progress bus (one `asyncio.Queue` per scan plus a list of past events for replay), `start_scan()` with `asyncio.create_task(run_pipeline(scan_id))`, and the orchestration in §5 with per-collector timeouts (§3 table). Collectors that aren't built yet return `unknown` checks. Save `internal` and `report` on the scan row, then emit `complete`; mark the scan `failed` only if steps 1–2 fail. `POST /api/scans` now runs the real pipeline unless demo mode applies (task 8).

Acceptance: a real café produces a report with the Google chapter scored and everything else `unknown`, and the SSE steps arrive.

### Task 4 · Reviews and competitors (hour 6–9)

- `collectors/competitors.py`: Nearby Search (New) for the business type, 1.5 km radius, ranked by popularity, top 3, Place Details for each.
- `collectors/reviews.py`: R01–R05 per §3.2. SerpApi `google_maps_reviews` sorted newest first. Verify whether `place_id` is accepted; otherwise look up the `data_id` once with `engine=google_maps`. Cache every SerpApi response; the free plan has about 250 searches a month. Fall back to Places reviews for R03.

### Task 5 · Website (hour 9–12)

`collectors/website.py` per §3.3:
- pages from the sitemap or nav links
- raw `httpx` fetch, `looks_empty`, and a lazy, reused Playwright browser with a 15 s render limit
- robots.txt per user agent, sitemap, JSON-LD
- all links (pass social links to the social collector)
- PageSpeed (mobile, performance, 40 s, falling back to time to first byte)
- one L2 extraction into `WebsiteFacts`, with `page_with_basics`

Then checks C01–C08 and T01–T09, and the T-gate cap. Save the website facts in `internal` (Dev A's info page reads them through `load_facts`).

### Task 6 · Live test, rivals, re-tests → gate 2 (hour 12–14)

- `collectors/live_test.py` per §3.8: L5 generates 12 prompts in 3 groups; 36 `grounded_call`s; mention by place ID or fuzzy name; position; others; facts check; and sources, with web URIs resolved by following the redirect (no body). Aggregate with the 2-of-3 rule; score 70 / 15 / 15. It starts right after the canonical profile with a 75 s timeout.
- Rivals: the top 3 from the live test get Place Details; build the `Comparison` (`insights_ro`, `actions` from templates).
- `POST /gemini-test` reruns only the live test and recomputes. `POST /rescan` starts a new scan with the same inputs.

**Gate 2:** `POST /api/scans` for a real café returns a complete report in under 90 s. Push and tell me "gate 2: real scan works", with the scan ID.

### Task 7 · Remaining collectors (hour 14–18)

- `collectors/training_probe.py` (§3.7): two prompts × 3 runs with no tools, plus one L7 judge call.
- `collectors/mentions.py` (§3.5): five Search-grounded queries; domains from chunk titles; follow redirects for URLs; filter; L4 classify; M01, M02, M03, M05.
- `collectors/social.py` (§3.6): Business Discovery for the Instagram handle (personal account or no token → fallbacks), cross-links from the website links, S02–S05. No Facebook anywhere.
- `collectors/listings.py` (§3.4): owner and website links only; fetch, L3 extract, normalize, compare; L01, L02 with per-field problems `L02:<source>:<field>`.

### Task 8 · Demo safety → gate 3 (hour 18–20)

- Demo mode: with `DEMO_MODE=fixture`, a scan whose `place_id` equals `DEMO_PLACE_ID` returns `fixtures/boema_report.json` (with a fresh `scan_id` and `checked_at`) and replays the SSE steps over about 8 s. `gemini-test` on it returns the same block after a short delay.
- Check the backoff and timeouts on every external call, and that a failed collector never fails the scan.
- Record a real scan of the chosen demo café and save it as the fixture. Confirm the demo works with Wi-Fi off (served from `cache/` and the fixture).

**Gate 3:** feature freeze. Tell me "gate 3 ready".

### Task 9 · Bugs (hour 20–22)

Fix what the demo run shows. Re-record the fixture if the data changed.

## Rules for you

- Nothing may bill, except grounded calls on `GEMINI_GROUNDED_API_KEY` for the scans named above (see "Working alongside Dev A").
- Scores come only from `scoring.py`; LLM output is turned into booleans or extracted values before any check uses it.
- Live-test calls: only the customer's question, no system prompt, no business context.
- `unknown` is never a fail: excluded from the score and listed in `Chapter.unknown` with a `reason_ro`.
- Every `CheckResult` stores evidence (found, expected, URL).
- Run Uvicorn with one worker; don't use `--reload` while testing a full scan.
- A contract change after gate 1 is additive only: `docs/contract.md` and `models.py` in one commit starting `contract:`, and tell me so I can tell Dev A to regenerate types.
- If Dev A's stub routes need a change, don't edit them after gate 1; tell me instead.
