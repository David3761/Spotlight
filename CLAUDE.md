# Marketingadvisor

Hackathon project: a Romanian web app that audits how visible a local business is in Gemini and tells the owner what to fix. Next.js frontend in `frontend/`, FastAPI backend in `backend/`, built by two devs in parallel, each with their own Claude Code session. Both sessions follow every rule in this file.

## Read before working

- `docs/architecture.md` — the plan, the team split, file ownership, build order and gates.
- `docs/contract.md` — every endpoint, response shape and shared Python interface. Code must match it exactly.
- `docs/data-collection-algorithm.md` — checks, data sources, points, weights, pipeline.
- `docs/sync.md` — messages between the two devs: read the entries addressed to you at the start of every task, answer there.
- `design/README.md` and `design/*.dc.html` — layout, Romanian copy and tokens (UI work).
- Your own prompt: `docs/prompts/dev-a-frontend.md` or `docs/prompts/dev-b-backend.md`.

## How to work

### Questions

- Ask all your questions together at the start, before writing code. Gaps in the plan are your dev's call, not yours.
- If a question comes up later, don't stop: finish everything that doesn't depend on it, then ask at the end, together with any other open points.
- When you tell your dev something non-obvious, say how you confirmed it.

### Never guess

A guessed value, behaviour, name or requirement costs a rework when it's caught and a bug when it isn't.

- Take values from their source: layout, sizes, colours and copy from `design/`; fields, paths and errors from `docs/contract.md`; behaviour from the docs and your prompt. What you remember about a library isn't a source, because versions change.
- When unsure, find out in this order: search the repo; read the installed package's source (`node_modules/`, the uv environment) at the locked version; read the official documentation; write a small throwaway script and run it.
- If it still isn't settled, it's a question (see above). Never present an assumption as a fact.

### Git

- Commit and push yourself, in small commits, after every task. Work on `main`; don't create or switch branches.
- Run `git pull --rebase` before starting each task and before every push, because the other dev pushes often. Never force-push.
- Never commit secrets, `.env` files, local databases, caches or throwaway scripts.

### Real calls and billing

- Run anything that doesn't bill: local servers, tests, free API quotas, cached responses.
- Before calling a paid service, check its free quota and stay inside it; cache every response so repeats cost nothing. Never upgrade a plan.
- Extraction, texts and chat use the free-tier `GEMINI_API_KEY` (an AI Studio project with no billing). Grounded calls (live test, mentions) go through Google Cloud (Vertex AI) on Dev B's free-trial project, with `GEMINI_MODEL_LIVE` (`gemini-3.5-flash-lite`), signed in with Application Default Credentials (`gcloud auth application-default login`) and `GOOGLE_CLOUD_PROJECT`; the trial credit pays, and nothing reaches a card unless someone clicks „Upgrade”. Cache every grounded response and run real scans only when you need them.

### Agents

- Spawn as many agents as help (parallel research, independent screens or modules, testing). Prefer the cheapest model that handles the task with room to spare: Sonnet for well-defined work, the session's model when the task needs judgment.
- Brief each agent completely, since it can't see your conversation: its goal, the files it owns, the docs to read, this file's rules, and what to return. Ask for raw facts and a list of what it couldn't settle, not guesses.
- Only one agent writes a given file. Agents don't install dependencies, commit or push; you do, after checking their work.

### Verify, review, hand off

- Before every commit: the type checker and linter report nothing (`npx tsc --noEmit` and `npm run lint` in `frontend/`; tests in `backend/` with `uv run pytest`). Reproduce logic you can't check by reading (parsing, state changes, races) with a throwaway test and fake clients.
- Throwaway scripts and tests go outside the repo (your scratchpad). If one has to sit in the repo to run, delete it before you commit.
- When the task is finished, run a code review (`/code-review` at high effort) and fix whatever it flags, then verify again.
- End with a short summary for your dev: what works now, decisions made along the way, what you couldn't check, and your open questions.
- When your dev corrects something that could happen again, propose adding it to this file.

## File ownership

| Owner | Paths |
| --- | --- |
| Dev A | `frontend/**`, root `package.json` and `package-lock.json`, `backend/app/api/fixes.py`, `backend/app/api/chat.py`, `backend/app/fixes/**`, `backend/app/assistant/**`, `backend/app/llm/prompts/fix_*`, `backend/app/llm/prompts/assistant_*` |
| Dev B | everything else in `backend/**` (incl. `pyproject.toml`, `uv.lock`, `.env.example`, `models.py`, `db.py`, `llm/client.py`, `services/`, `pipeline/`, `fixtures/`), `docs/contract.md` (Dev A may edit its Fixes and Assistant sections) |
| Both must agree | `docs/architecture.md`, `docs/data-collection-algorithm.md`, `CLAUDE.md`, `README.md`, `.gitignore` |

Never edit a file the other dev owns. If you need something changed there, finish what you can and list it in your questions for your dev.

## Project rules

- Contract changes after gate 1: additive optional fields only, `docs/contract.md` and the Pydantic model in the same commit, message starting `contract:`.
- Scores come only from `backend/app/pipeline/scoring.py`. The LLM never sets or adjusts a score.
- Live-test Gemini calls carry only the customer's question: no system prompt, no business context.
- Fetch websites with `httpx`; start Playwright only for pages whose raw HTML comes back empty.
- UI text is Romanian, copied from `design/*.dc.html` where it exists (with the changes listed in `docs/architecture.md` → "Where the build differs from the design"). Code, identifiers and commit messages are English. Light mode only.
- `backend/.env` is shared by both devs' backend code; `frontend/.env.local` holds only `NEXT_PUBLIC_API_URL`. Neither is committed. `backend/.env.example` has the same names, with values only for non-secret settings.

## Development rules

### Build only what's needed, and build it once

- No speculative abstractions, options or parameters, no parameters every caller passes the same way, no code that has no effect, no features the plan doesn't ask for.
- Reuse before you write: search the repo for a component, helper or type that already does the job.
- Don't duplicate. When a second place needs the same thing, extract it once and use it from both, with a parameter only for differences a user would actually see. When you add a function, point existing code that does the same job at it and delete the copy.
- Don't extract a 1–2 line function that has one caller; inline it. Don't wrap a short shared sequence in a helper that takes a callback; write the steps out in each place.
- Don't copy an older pattern that breaks these rules or the architecture; follow the rules and point out the difference.

### Architecture

- Frontend: requests only in `src/lib/api.ts`; state, loading and errors in hooks; components render UI and hold short-lived UI state only. Contract types (`src/lib/types.ts`) are the app's models.
- Backend: routers parse the request and call a service; services hold the logic; data access goes through `app/db.py` and `app/services/resolution.py`. Routers don't contain business logic.
- Logic that takes only one model's data belongs with that model: a property or method on a Python model, a function next to the type in TypeScript, not inside a component.
- Turn exceptions into user messages in one place at the boundary (the API error handler, the frontend's error display), not in every call.

### Naming and structure

- Plain domain nouns (`ChapterCard`, `isEmpty`), not metaphors. No 1-letter names, also in callbacks (`problem`, not `p`). Name unused parameters `_`.
- Functions that take arguments and return data start with `get` (`getChapterLabel(id)`); parameterless getters are nouns; actions are verbs.
- Required parameters and props first, then optional ones; callbacks last in each group. A callback every caller passes is required, not optional.
- In data models the ID field comes first.
- Order functions in call order, and components in on-screen order (the main component first, sub-components after it in the order they appear).
- Literal unions and enums instead of magic strings. Constants live in the file that uses them; no global constants file.

### Code style

- Let inference work: no explicit type when the initializer makes it obvious (`const isOpen = false`). Keep explicit types on function signatures and exported values.
- No non-null assertions (`value!`): check the value and let the type narrow.
- Always use braces around `if`/`else` bodies. Use an early return instead of deep nesting.
- Pass functions by reference (`onClick={handleSubmit}`), not through forwarding arrows (`() => handleSubmit()`), unless you transform arguments.
- An arrow function whose body would wrap gets a block body.
- A function that awaits nothing isn't `async`.
- Write computed literals, not inline arithmetic for fixed values (`width: 60`, not `100 - 20 * 2`).

### Comments and docs

- Every declaration you add gets a one-line doc comment: `/** … */` in TypeScript (components, functions, types, props fields, module constants), a docstring in Python (functions, classes, modules' public constants). Locals are exempt.
- Start functions with a third-person verb (`Returns …`, `Marks …`), fields with `The …`, components with `A component that …`. End with a period; wrap `true`, `false` and `null` in backticks.
- Describe the role, not the values the code already shows (no pixel sizes, hex codes, durations). Two lines only for a non-obvious why.
- No comments that talk to the reader of the chat ("TODO: swap later", notes on what changed, names of people or conversations). Config and env files stay bare.

### UI

- Exact values from the design: hex colours and font weights from the artboards and `design/README.md`. If a colour isn't a token yet, add a token; don't reuse a similar one.
- Logical directions (`ps-`, `pe-`, `ms-`, `me-`, `start-`, `end-`), not left/right.
- Buttons for actions, links for navigation, `aria-current` on the active nav item, visible focus.
- Every request-backed screen has separate loading, empty, error and retry states; a failed load is never shown as an empty list or an endless spinner.
- Error messages must be true for every cause ("Nu am putut contacta serverul", not "Nu ai internet").
- Text wraps instead of clipping at large zoom and on 390 px screens; never fix the height of a text input.
- Debounce and throttle in the component, not in the data layer.

### Dependencies

- Before adding a package, check its last publish date (`npm view <name> time.modified`, PyPI) and prefer ones updated in the last 5 months. Say the date when you add it.
- Don't add a package for a small feature.

## Running

- Everything: `npm run dev` at the repo root (frontend on :3000, backend on :8000).
- Backend alone: `cd backend && uv run uvicorn app.main:app --port 8000` (single worker; avoid `--reload` while a scan runs).
- Frontend alone: `cd frontend && npm run dev`.
- Regenerate API types (backend running): `cd frontend && npm run gen:api`.
