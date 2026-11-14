# Demo click path

*Hackathon presentation, about 5 minutes, on Dev B's laptop. It runs from Origo's recorded real scan; a live scan is a bonus.*

## On the day, before going on stage

1. `backend/.env`: `DEMO_MODE=fixture`, `DEMO_PLACE_ID=ChIJQbgapEH_sUAR__vch8jUosQ` (Origo).
2. `npm run dev` at the repo root; wait for both servers.
3. **Rehearse the whole path below once, online, on this laptop.** Every text and answer it generates is cached in `backend/cache/`, and later runs replay them in under a second, even with Wi-Fi off. The rehearsal matters for three reasons:
   - The smart model allows only 20 requests a day on the free key, and both devs share that key. One rehearsal uses about 7, so keep other smart-model calls (fix texts, info pages, chat) to a minimum that day.
   - The first info page takes about 30 seconds to write, and each fix text 10–30 seconds.
   - The cache only matches identical input. On stage, click the same tones in the same order and type the assistant message exactly as written here.
4. Open `http://localhost:3000/start` in a fresh browser window at desktop width.
5. Turn off sleep and notifications. Keep the phone hotspot ready for a live scan.

## The path

1. **Onboarding (`/start`).**
   - Answers:
     - Name „Origo”.
     - Type „Cafenea”.
     - City „București”, neighbourhood „Centrul Vechi”.
     - Website: „Da”, then `origocoffee.ro`.
     - Google Maps: „Caută-mă pe Google”, then „Asta sunt eu” on the first card.
     - Quick questions: claimed „Da”, description „Nu” (this keeps G08 open for step 7), last post „Mai demult”.
     - Instagram `instagram.com/origo_coffee`; skip TikTok.
     - Last social post „Luna asta”, then „Nu folosesc altele”.
   - Press „Gata, analizează afacerea”.
   - Say: the onboarding is a short chat, and the card on the right fills in as you answer.
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

## If something breaks

- **A live scan of a judge's business errors or stalls:** go back to the Origo dashboard tab without comment.
- **A fix text or the info page shows „Nu am putut contacta Gemini acum”:** the day's smart-model quota is used up, or there's no internet. Skip to the next step. Steps 1–4 and „Am rezolvat” don't call Gemini.
- **The page doesn't load:** restart with `npm run dev` (a few seconds).
