# Demo click path

*Hackathon presentation, about 5 minutes. Runs from the recorded demo scan; a live scan is a bonus.*

## Before going on stage

- `backend/.env`: `DEMO_MODE=fixture`, `DEMO_PLACE_ID` = the demo café's place ID.
- `npm run dev` at the repo root; wait for both servers.
- Open `http://localhost:3000/start` in a fresh browser window at desktop width.
- Laptop: sleep off, notifications off, phone hotspot ready.

## The path

1. **Onboarding (`/start`).** Type the demo café's name, pick „Cafenea”, enter the city and neighbourhood, say yes to the website and paste its address. At the Google Maps step press „Caută-mă pe Google” and pick „Asta sunt eu” on the first card. Answer the three quick questions (claimed: Da, description: Nu, last post: Mai demult), paste the Instagram link, skip TikTok, pick the platforms, then „Gata, analizează afacerea”.
   - Say: the onboarding is a short chat, and the card on the right fills in as you answer.
2. **Loading.** The five steps tick off in about 8 seconds (Google, Recenzii, Website, Rețele sociale, Gemini).
   - Say: we read the Google profile, the reviews, the website and Instagram, and we ask Gemini 12 questions a customer would ask.
3. **Dashboard.** Point at the overall score, „Apari în X din 12 răspunsuri” and the three competitors Gemini recommends instead, then „Următorii pași”.
4. **Vizibilitate în Gemini.** Open „Vezi răspunsurile”. Show one question where the café doesn't appear, who Gemini recommended, and the sources with Google Maps under it. Scroll to „De ce îi alege Gemini pe ei?”.
5. **Fix with generated text.** Open „Rețele sociale” in the sidebar → „Rezolvă” on the Instagram bio. Switch tone to „Profesionist”, press „Generează din nou”, then „Am rezolvat”: the ring fills, the toast shows the points, the sidebar count drops.
6. **Info page for the website.** Open „Site-ul, văzut de Gemini” → the info page problem. Show the page with the yellow fields to fill in, then „Trimite persoanei care îți face site-ul”.
7. **Assistant.** Open „Conversații” → „Conversație nouă”, type „Am pus descrierea pe Google”. When the assistant offers „Da, marchează-l”, press it: scores rise and the assistant suggests the next step. Show „Anulează” if there's time.

## If something breaks

- A live scan of a judge's business errors or stalls: go back to the demo café's dashboard tab without comment.
- The page doesn't load: restart with `npm run dev` (a few seconds).
