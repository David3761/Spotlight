# Status

The board of everything left before the demo. Both devs keep it current: change your row in the same commit as the work, and put questions and answers in [sync.md](sync.md), not here. States: `todo`, `doing`, `blocked` (say on what), `done` (with the date).

Last full sync: 14 November 2026, started by Dev A; waiting for Dev B to confirm or correct the Dev B rows.

## Where things stand

- **Dev A:** tasks 1–8 are done: onboarding, loading, dashboard, chapters, the four fix panels, the Gemini screen, the assistant, and the fixes and assistant backends. Dev A also built Dev B's Task 7: social, listings, mentions and the training probe.
- **Dev B:** tasks 1–5 are done: skeleton, Places, Google profile, pipeline, reviews, competitors and website. Rescan is real.
- **A real scan today** (Origo, 14 s) scores every chapter except „Mențiuni”, which needs the gcloud login. The Gemini block stays `unknown` until the live test lands.

## Dev B

| # | Item | State | Notes |
| --- | --- | --- | --- |
| B1 | `collectors/live_test.py` (§3.8): L5 prompts, 36 Maps-grounded calls, matching by place ID or name, 2-of-3 aggregation, score 70 / 15 / 15 | todo | Needs a machine with the gcloud login |
| B2 | Rivals: Place Details for the live test's top 3 → `Comparison` with `insights_ro` and `actions` | todo | |
| B3 | Real `POST /gemini-test`: rerun only the live test and recompute | todo | Today it's a 2 s stub that only updates `last_checked` |
| B4 | Wire the live test into the `gemini` step next to the probe, and set its done text | todo | The text now says „I-am pus lui Gemini 6 întrebări” when only the probe ran |
| B5 | Run one real scan on the gcloud machine and check mentions (M01–M05) | todo | The only Task 7 collector not yet run live |
| B6 | Gate 2: a real café completes in under 90 s with the live test; post the scan ID in sync.md | todo | After B1–B4 |
| B7 | Demo mode: `gemini-test` on a demo scan returns the fixture's block after a short delay | todo | Task 8 |
| B8 | Check backoff and timeouts on every external call | todo | Task 8 |
| B9 | Record the demo café's real scan as the fixture (`boema_report.json`, `boema_checks.json`, facts) | blocked | Needs the demo café (O1). The current fixture still has `L02:website:name`, which real scans no longer produce |
| B10 | Gate 3, backend side: the demo works with Wi-Fi off (cache plus fixture) | todo | After B7–B9 |

## Dev A

| # | Item | State | Notes |
| --- | --- | --- | --- |
| A1 | Gate 2: run a real scan through onboarding and fix what renders wrong on every screen, the Gemini screen with real live-test data in particular | blocked | Waiting on B1–B4 |
| A2 | Real scans with no website and with no Google profile, through every screen | todo | |
| A3 | Offline demo: cache the assistant's Gemini turns so a rehearsed conversation replays with Wi-Fi off, and pre-warm the fix texts and info page the demo uses | todo | Fix texts and the info page are already cached; the assistant isn't |
| A4 | Put the app name in `frontend/src/config.ts` | blocked | Needs the name (O3) |
| A5 | Update `docs/demo.md` for the demo café and rehearse it with `DEMO_MODE=fixture` and Wi-Fi off | blocked | Needs O1, B9 and A3 |
| A6 | Mobile pass at 390 px against the `M*` artboards | todo | Low priority, at the owners' request |

## Owners (the two humans)

| # | Item | State | Notes |
| --- | --- | --- | --- |
| O1 | Pick the demo café: it needs a website and an Instagram business or creator account. Put its place ID in `DEMO_PLACE_ID` in both `.env` files | todo | Unblocks B9 and A5 |
| O2 | Send `META_ACCESS_TOKEN` and `META_IG_USER_ID` to Dev B privately and put them in Dev A's `.env` | todo | Without them the Instagram bio check (S05) stays `unknown` and S03 uses the owner's answer |
| O3 | Choose the app name (now „[Nume aplicație]”) | todo | Unblocks A4 |
| O4 | Decide which laptop runs the demo. If „Testează din nou” or a live scan has to work on stage, that laptop needs `gcloud auth application-default login` on Dev B's project; otherwise the demo runs from the fixture only | todo | |
| O5 | Dev B's open question to their dev: approve the gcloud command in Claude Code, or run the real scans by hand | todo | Blocks B1 and B5 |
