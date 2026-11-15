# Demo click path

*Hackathon presentation, about 5 minutes, on Dev B's laptop. It runs from Origo's recorded real scan; a live scan is a bonus.*

## On the day, before going on stage

1. `backend/.env`: `DEMO_MODE=fixture`, `DEMO_PLACE_ID=ChIJQbgapEH_sUAR__vch8jUosQ` (Origo).
2. `npm run dev` at the repo root; wait for both servers.
3. **Rehearse the whole path below once, online, on this laptop.** Every text and answer it generates is cached in `backend/cache/`, and later runs replay them in under a second, even with Wi-Fi off. The cache only matches identical input, so on stage click the same tones in the same order and type the assistant message exactly as written here. Without the rehearsal, the info page takes about 10 seconds and each fix text a few seconds, and nothing works offline.
4. Open `http://localhost:3000/start` in a fresh browser window at desktop width.
5. Turn off sleep and notifications. Keep the phone hotspot ready for a live scan.
6. For step 8 (optional): the presenter's phone number must be verified on the WhatsApp test number, and the presenter sends „Start” to that number from WhatsApp less than 24 hours before going on stage. Without it, WhatsApp refuses the message and the card says so.

## The path

1. **Onboarding (`/start`).** Gemini leads the chat. Type and click exactly this, in this order: offline, only the rehearsed chat replays.
   - Type „Origo, o cafenea de specialitate în Centrul Vechi, București”. Name, type and location fill in on the card at once.
   - Type „da, origocoffee.ro”.
   - Press „Asta sunt eu” on the Origo card.
   - Chips: „Da” (claimed), „Nu” (description: this keeps G08 open for step 7), „Mai demult” (last Google post).
   - Type „pe insta suntem @origo_coffee, tiktok n-avem”.
   - Chip „Luna asta”, then „Nu folosesc altele”, then „Gata, analizează afacerea”.
   - Say: you just talk to it like to a person. Gemini understands loose answers, asks only what's missing, and the card on the right fills in as you go.
2. **Loading.** The five steps tick off in about 8 seconds (Google, Recenzii, Website, Rețele sociale, Gemini).
   - Say: we read the Google profile, the reviews, the website and Instagram, and we ask Gemini 12 questions a customer would ask.
3. **Dashboard.** Point at:
   - The overall score, 74.
   - „Apari în 5 din 12 răspunsuri”, and the three places Gemini recommends instead: Arcade Cafe, Artichoke, Cafeneaua ART-AN-TE.
   - „Următorii pași”.
4. **Vizibilitate în Gemini.**
   - Open „Vezi răspunsurile”.
   - In „Cartier”, show „cafenea în centrul vechi”: Origo doesn't appear, and Gemini recommended Grand Café Van Gogh, Cafeneaua Veche 9 and Arcade Cafe, with the Google Maps sources under it.
   - Scroll to „De ce îi alege Gemini pe ei?”.
5. **Fix with generated text.**
   - Open „Rețele sociale” in the sidebar, then „Rezolvă” on the Instagram bio.
   - Switch the tone to „Profesionist” and press „Generează din nou”.
   - Press „Am rezolvat”: the chapter goes from 75 to 100, the toast shows the points, and the sidebar count drops.
6. **Info page for the website.**
   - Open „Site-ul, văzut de Gemini”, then the problem „Gemini nu găsește o pagină cu informațiile de bază”.
   - Show the page with the yellow field to fill in (holiday hours), then „Trimite persoanei care îți face site-ul”.
7. **Assistant.**
   - Open „Conversații”, then „Conversație nouă”, and type exactly „Am pus descrierea pe Google”.
   - When the assistant offers to mark it, press the confirm chip: the scores rise, and the assistant suggests the next step.
   - Show „Anulează” if there's time.
8. **WhatsApp reply suggestions (optional, needs the internet).**
   - Open „Recenzii”. In the „Răspunsuri sugerate pe WhatsApp” card, type the presenter's number and press „Pornește”.
   - Press „Simulează o recenzie nouă”: the presenter's phone gets the newest real review with a suggested reply.
   - Say: when a new review comes in, the owner gets a reply ready to copy, right on WhatsApp.

## If something breaks

- **A live scan of a judge's business errors or stalls:** go back to the Origo dashboard tab without comment.
- **A fix text or the info page shows „Nu am putut contacta Gemini acum”:** the free key's daily quota is used up, or there's no internet. Skip to the next step. Steps 1–4 and „Am rezolvat” don't call Gemini.
- **The page doesn't load:** restart with `npm run dev` (a few seconds).
