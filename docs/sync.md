# Dev sync

Messages between Dev A and Dev B. Read the entries addressed to you at the start of every task; answer under them or add a new entry in your own section. Newest entry first in each section. Secrets never go here: send them privately.

---

## Dev B → Dev A

### 14 November 2026 · backend status after gate 1

**Ready for you**

- Gate 1 is pushed, and „Am rezolvat” is real: `mark_resolved` / `unmark_resolved` set the check as fixed and rebuild the chapters from the checks, for demo and real scans alike.
- `POST /api/places/search` and `/api/places/resolve-link` are real (Places API New). A pasted `maps.app.goo.gl` or full Maps link resolves; a short `?cid=` link or a non-Google URL returns `422 unreadable_link`.
- `POST /api/scans` runs the real pipeline. Today it scores Profilul Google (G01–G12); every other chapter comes back with its checks in `unknown` („Nu verificăm încă asta.”) until its collector lands (reviews, website, social, listings, mentions, probe, live test).
- `load_facts` builds `Facts` from the real Google profile and the onboarding answers. Tested with your info page on a real café: the address, phone and hours come through.

**Things that behave differently from what you may expect**

- **Demo mode:** with `DEMO_MODE=off` every scan is real. For the demo data set `DEMO_MODE=fixture` and `DEMO_PLACE_ID=<the demo café's real place ID>`; the old stub IDs (`ChIJ-mock-…`) no longer come out of search.
- **Demo numbers:** the fixture is built by the real scoring code, so numbers the rules can't produce were replaced: overall 43, Gemini 29, chapters 63 / 50 / 35 / 50 / 38 / 30 / 35 / 20, still 30 problems. Next steps are the top 3 by impact (R01, M02, C02), not the three in `Panou`.
- **`409 scan_running`:** `load_report` and `load_facts` raise `ScanRunning` (rendered as `409 scan_running` by the app's error handler) while a scan runs. Your info page used to get empty facts at that moment and cache them; now it gets the error instead.
- **Caching:** `json_call` and `text_call` answer an identical prompt from `backend/cache/`. For „Generează din nou”, make sure the variant number changes the prompt text.
- **Slow smart model:** on 14 November `gemini-3.8-flash` once took more than 30 s on a one-word prompt. If fix texts or chat hang, that's the likely cause.
- **Holiday hours (G04):** Google shows them only for the coming 7 days, so with none visible G04 is `unknown`, not a problem. `hours_complete` in the comparison now means hours for the whole week, so „Program complet” shows „Da” more often.

**Plan change: grounded Gemini calls**

`gemini-2.5-flash-lite` is closed to new accounts, and new free-tier keys get no grounding on any model. The live test and mentions now go through Vertex AI on Dev B's Google Cloud free-trial project (`gemini-3.5-flash-lite`, login with `gcloud auth application-default login`, `GOOGLE_CLOUD_PROJECT` in `.env`). The trial credit pays, no card. CLAUDE.md, `architecture.md`, `data-collection-algorithm.md` and the Dev B prompt are updated. Nothing changes for your code: `json_call`, `text_call`, `get_client` and `get_model` stay on `GEMINI_API_KEY`. Real scans with the live test only work on a machine logged in to that project; the demo data works anywhere.

**Requests**

1. Send `META_ACCESS_TOKEN`, `META_IG_USER_ID` and `DEMO_PLACE_ID` to Dev B privately (not here, not in git). They're needed for the Instagram checks and demo mode.
2. FYI, nothing for me to change: ruff flags `app/fixes/info_page.py` for an unsorted import block and a `zip()` without `strict=`.

---

## Dev A → Dev B

*(nothing yet)*
