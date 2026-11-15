# Demo click path

*Hackathon presentation, about 5 minutes, on Dev B's laptop. It runs from Bike Explorer's recorded real scan; a live scan is a bonus.*

Bike Explorer is a bike repair shop at Strada Mihail Petrescu 2A, Berceni, București (bikexplorer.ro, no Instagram or TikTok).

## On the day, before going on stage

1. `backend/.env`: `DEMO_MODE=fixture`, `DEMO_PLACE_ID=ChIJO0dkNFD-sUARiznQlhEdZcM` (Bike Explorer).
2. `npm run dev` at the repo root; wait for both servers.
3. **Rehearse the whole path below once, online, on this laptop.** Every text and answer it generates is cached in `backend/cache/`, and later runs replay them in under a second, even with Wi-Fi off. The cache only matches identical input, so on stage click the same tones in the same order and type the messages exactly as written here. Without the rehearsal, the info page takes about 10 seconds and each fix text a few seconds, and nothing works offline.
4. Open `http://localhost:3000/start` in a fresh browser window at desktop width.
5. Turn off sleep and notifications. Keep the phone hotspot ready for a live scan.
6. For step 8 (optional): the presenter's phone number must be verified on the WhatsApp test number, and the presenter sends „Start” to that number from WhatsApp less than 24 hours before going on stage. Without it, WhatsApp refuses the message and the card says so.

## The path

1. **Onboarding (`/start`).** Gemini leads the chat. Type and click exactly this, in this order: offline, only the rehearsed chat replays.
   - Type „Bike Explorer, un service de biciclete în Berceni, București”. Name, type and location fill in on the card at once.
   - Type „da, bikexplorer.ro”.
   - Press „Asta sunt eu” on the Bike Explorer card.
   - Chips: „Da” (claimed), „Nu” (description: this keeps G08 open for step 5), „Mai demult” (last Google post).
   - Type „n-avem instagram sau tiktok, doar site-ul”.
   - „Nu folosesc altele”, then „Gata, analizează afacerea”.
   - Say: you just talk to it like to a person. Gemini understands loose answers, asks only what's missing, and the card on the right fills in as you go.
2. **Loading.** The five steps tick off in about 8 seconds (Google, Recenzii, Website, Rețele sociale, Gemini).
   - Say: we read the Google profile, the reviews, the website and the social links, and we ask Gemini 12 questions a customer would ask.
3. **Dashboard.** Point at:
   - The overall score, 55.
   - „Apari în 6 din 12 răspunsuri”, and the three shops Gemini recommends instead: Fix Your Bike, COBI Custom Bicycle, Sir Fixalot.
   - „Următorii pași”: no Instagram, and not in any „best of” list.
4. **Vizibilitate în Gemini.**
   - Open „Vezi răspunsurile”.
   - In „General”, show „service de biciclete bucuresti”: Bike Explorer isn't in any of the 3 answers, and Gemini recommended COBI Custom Bicycle, Fix Your Bike and FreeRideBikes, with the Google Maps sources under it.
   - Scroll to „De ce îi alege Gemini pe ei?”: Bike Explorer has a 5.0 rating and 195 reviews, more than Fix Your Bike (91) and Sir Fixalot (84).
5. **Fix with generated text.**
   - Open „Profilul Google” in the sidebar. Point at „Categoria de pe Google nu se potrivește”: Google lists the shop as „Servicii”. It comes back in step 7.
   - Press „Rezolvă” on „Fără descriere a afacerii”.
   - Switch the tone to „Profesionist” and press „Generează din nou”.
   - Press „Am rezolvat”: the chapter goes from 61 to 72, the toast shows the points, and the sidebar count drops.
6. **Info page for the website.**
   - Open „Site-ul, văzut de Gemini”, then the problem „Gemini nu găsește o pagină cu informațiile de bază”.
   - Show the page with the yellow field to fill in (holiday hours), then „Trimite persoanei care îți face site-ul”.
7. **Assistant.**
   - Open „Conversații”, then „Conversație nouă”, and type exactly „Am schimbat categoria pe Google în Service de biciclete”.
   - The assistant offers to mark the category problem. Press „Da, marchează-l”: Profilul Google rises again, and the assistant suggests the next step.
   - Show „Anulează” if there's time.
8. **WhatsApp reply suggestions (optional, needs the internet).**
   - Open „Recenzii” (every check there passes, so it shows as solved). In the „Răspunsuri sugerate pe WhatsApp” card, type the presenter's number and press „Pornește”.
   - Press „Simulează o recenzie nouă”: the presenter's phone gets the newest real review with a suggested reply.
   - Say: when a new review comes in, the owner gets a reply ready to copy, right on WhatsApp.

## If something breaks

- **A live scan of a judge's business errors or stalls:** go back to the Bike Explorer dashboard tab without comment.
- **A fix text or the info page shows „Nu am putut contacta Gemini acum”:** the free key's daily quota is used up, or there's no internet. Skip to the next step. Steps 1–4 and „Am rezolvat” don't call Gemini.
- **The page doesn't load:** restart with `npm run dev` (a few seconds).
