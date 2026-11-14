# Marketingadvisor

Hackathon project: a Romanian web app that audits how visible a local business is in Gemini and tells the owner what to fix. Next.js frontend in `frontend/`, FastAPI backend in `backend/`, built by two devs in parallel, each with their own Claude Code session.

## Read before working

- `docs/architecture.md` — the plan, the team split, file ownership, build order and gates.
- `docs/contract.md` — every endpoint and response shape. Code must match it exactly.
- `docs/data-collection-algorithm.md` — checks, data sources, points, weights, pipeline.
- `design/README.md` and `design/*.dc.html` — layout, Romanian copy and tokens (UI work).
- Your own prompt: `docs/prompts/dev-a-frontend.md` or `docs/prompts/dev-b-backend.md`.

## File ownership

| Owner | Paths |
| --- | --- |
| Dev A | `frontend/**`, root `package.json` and `package-lock.json`, `backend/app/api/fixes.py`, `backend/app/api/chat.py`, `backend/app/fixes/**`, `backend/app/assistant/**`, `backend/app/llm/prompts/fix_*`, `backend/app/llm/prompts/assistant_*` |
| Dev B | everything else in `backend/**` (incl. `pyproject.toml`, `uv.lock`, `models.py`, `db.py`, `llm/client.py`, `services/`, `pipeline/`, `fixtures/`), `docs/contract.md` (Dev A may edit its Fixes and Assistant sections) |
| Both must agree | `docs/architecture.md`, `docs/data-collection-algorithm.md`, `CLAUDE.md`, `README.md`, `.gitignore` |

Never edit a file the other dev owns. If you need something changed there, stop and tell your dev what to ask for.

## Ground rules

- Contract changes after gate 1: additive optional fields only, `docs/contract.md` and the Pydantic model in the same commit, message starting `contract:`.
- Scores come only from `backend/app/pipeline/scoring.py`. The LLM never sets or adjusts a score.
- Live-test Gemini calls carry only the customer's question: no system prompt, no business context.
- Fetch websites with `httpx`; start Playwright only for pages whose raw HTML comes back empty.
- UI text is Romanian, copied from `design/*.dc.html` where it exists; code, identifiers and commit messages are English. Light mode only.
- Secrets live in `backend/.env` (shared by both devs' backend code) and `frontend/.env.local`, never in git. `backend/.env.example` has the same names, with values only for non-secret settings.
- Nothing may bill. Run anything that stays inside a free tier: local servers, free API quotas, cached responses. Check a service's free quota before calling it and cache every response. The only billed key is `GEMINI_GROUNDED_API_KEY` (grounded calls bill their tokens): use it only for the live test and mentions, and only for the real scans needed for gate 2 and the demo recording.
- No comments in code that talk to the reader of the chat ("TODO: swap later", tutorial notes). Write only comments that describe the code itself. Config and env files stay bare.
- Commit small and push to `main`. Run `git pull --rebase` before starting each task and before every push, because the other dev pushes often. Never force-push.

## Running

- Everything: `npm run dev` at the repo root (frontend on :3000, backend on :8000).
- Backend alone: `cd backend && uv run uvicorn app.main:app --port 8000` (single worker; avoid `--reload` while a scan runs).
- Frontend alone: `cd frontend && npm run dev`.
- Regenerate API types (backend running): `cd frontend && npm run gen:api`.
