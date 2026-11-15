# Spotlight: product description for the pitch

*Hackathon v1, built 14–15 November 2026. Every number in [§8](#8-the-demo-case-cafetăria-miciurin) comes from a real scan of Cafetăria Miciurin, a specialty café in Bucharest, recorded on 15 November 2026.*

The product is in Romanian. Screen labels are quoted in Romanian, with an English translation where it helps.

---

## 1. In one sentence

**Spotlight shows a local business owner whether Gemini recommends them when customers ask for a place like theirs, and walks them through the fixes, most valuable first, writing most of the texts for them.**

Shorter: *"Find out if Gemini recommends you, and fix it in minutes."*

---

## 2. The problem

- **People ask AI assistants where to go.** A customer types „cafenea liniștită în Centrul Vechi” ("a quiet café in the Old Town") into Gemini. Instead of ten links, they get back three or four names. If you aren't one of them, you don't exist for that customer.
- **Owners can't see any of this.** Nobody tells a café owner whether Gemini recommends them, for which questions, or who it recommends instead.
- **What decides it is scattered across many places:** the Google profile, the reviews and whether the owner answers them, what the website says (and whether an AI can even read it), the Instagram bio, whether the address and hours match everywhere, and whether other sites talk about the business.
- **Most of it is technical and in English.** robots.txt, structured data, crawlers, page speed. A café owner shouldn't need to know what JSON-LD is.
- **Being good isn't enough.** In our demo, a specialty café with a perfect 5.0 rating from 452 reviews is named in just 1 of Gemini's 12 answers, and not at all when someone asks for a specialty café in its own neighbourhood (see §8).

---

## 3. Who it's for

### Primary user: the owner of a local business in Romania

- Cafés, restaurants, bars, beauty salons, hotels, shops, repair shops and other local businesses.
- Runs the business alone or with a small team. No marketing department, no SEO budget.
- Not technical. Uses Google Maps, Instagram and WhatsApp on their phone.
- Has maybe 10 minutes between customers, so they need to know **what to do first**, not a 40-page audit.
- Often has "a person who does the website" (a friend, a freelancer) whom they'd happily forward instructions to.

### Secondary user: the owner's web developer

- Receives a ready-made document with the exact technical fixes, the evidence, and how to check each fix. They don't need to talk to the owner or the tool.

---

## 4. What it does, in short

1. **You talk to it.** A chat led by Gemini asks about your business in plain Romanian. You answer however you like; it understands loose answers and asks only what's still missing.
2. **It checks everything Gemini looks at.** It reads your Google profile, your Google reviews, your website, your Instagram, the other platforms you're on and mentions of you on other sites. That's 47 checks, in about 25 seconds.
3. **It asks Gemini what your customers ask.** It asks Gemini 12 real customer questions, three times each, and counts how often you're recommended and who is recommended instead.
4. **It gives you one score and a short to-do list.** One score out of 100, 8 simple chapters, and the three fixes that bring the most points.
5. **It does most of the work for you.** It writes your Instagram bio, Google description, review replies and website texts. It builds you an info page. It prepares a ready-to-send document for your web person.
6. **It tracks your progress.** Press „Am rezolvat” ("Done") or just tell the assistant what you did, and your score goes up at once.

---

## 5. The owner's journey, screen by screen

### Screen 1 · Setup (Configurare): a conversation, not a form

- Gemini opens with: „Bună! Spune-mi pe scurt despre afacerea ta: cum se numește, ce fel de afacere e și unde te găsesc clienții.” ("Hi! Tell me briefly about your business: what it's called, what kind of business it is and where customers find you.")
- The owner types freely, e.g. „Cafetăria Miciurin, o cafenea de specialitate în Domenii, București” ("Cafetăria Miciurin, a specialty café in Domenii, Bucharest"). Name, type, city and neighbourhood are all filled in from that one answer.
- A **business card** („Cartea de vizită”) beside the chat fills in live as the owner answers.
- **Finding the Google profile:** the app searches Google Maps and shows matching places as cards (name, address, rating, number of reviews, with „Cel mai probabil”, "Most likely", on the best match). The owner taps „Asta sunt eu” ("That's me"), says „da” or „primul” ("yes", "the first one"), or pastes a Google Maps link. If a link can't be read, the chat explains why instead of showing an error.
- **Quick-reply chips** under each question are shortcuts: „Da” (Yes), „Nu” (No), „Nu știu” (I don't know), „Luna asta” (This month), „Mai demult” (A while ago), „Niciodată” (Never), „Fără site” (No website), „Fără profil Google” (No Google profile), „Fără rețele” (No social media), „Nu folosesc altele” (I don't use any others).
- What it asks: name, type, city and neighbourhood, website, Google profile, three quick questions about the Google profile (is it claimed? does it have a description? when was the last post?), Instagram and TikTok links, when they last posted, and which other platforms they're on (TripAdvisor, Glovo, Wolt, Bolt Food, Booking, Booksy).
- Questions that don't apply are skipped. For example, with no Google profile, the Google questions are skipped.
- The owner ends with „Gata, analizează afacerea” ("Done, analyse my business").

### Analysis in progress

- Five steps tick off as each finishes, each with a short live result:
  - **Google**: „Am găsit Profilul tău Google” ("Found your Google profile")
  - **Recenzii** (Reviews): „Am găsit 452 de recenzii” ("Found 452 reviews")
  - **Website**: „Am citit cafetaria.ro” ("Read cafetaria.ro")
  - **Rețele sociale** (Social media): „Am verificat Instagram” ("Checked Instagram")
  - **Gemini**: „I-am pus lui Gemini 12 întrebări” ("Asked Gemini 12 questions")
- When it's done, the desktop moves on by itself; on a phone the owner taps „Vezi rezultatele” ("See the results").

### Screen 2 · Dashboard (Panou principal)

- **Overall score** in a ring that animates up to the number. The ring is red under 40, amber from 40 to 69 and green from 70.
- A **one-line verdict** under it, such as „Ești pe drumul bun. Câteva lucruri simple te pot aduce mai sus.” ("You're on the right track. A few simple things can take you higher.")
- A count of open problems ("20 de probleme de rezolvat") across 8 chapters.
- **Gemini visibility card:** „Apari în 1 din 12 răspunsuri” ("You appear in 1 of 12 answers"), plus „În locul tău, Gemini recomandă:” ("Instead of you, Gemini recommends:") with the three competitors it names most, and in how many answers.
- **„Următorii pași”** ("Next steps"): the three fixes that add the most points overall, each with its points badge (+100, +30, +56).
- **8 chapter cards**, each with its own score.
- **Assistant card:** „Spune-i asistentului ce ai făcut și îl marchează ca rezolvat. Îl poți întreba și ce să faci mai departe.” ("Tell the assistant what you did and it marks it as done. You can also ask it what to do next.")
- **„Analizează din nou”** ("Analyse again") runs a fresh scan with the same answers.

### Screen 3 · Chapter (Capitol)

- The chapter's score, a short plain-language intro on why it matters to Gemini, and an **„Unde se rezolvă”** ("Where you fix this") box, e.g. "In the Google Maps app, from the account you created the profile with."
- „+N puncte posibile” ("+N possible points") and „Scorul general ar crește cu aproximativ N puncte” ("Your overall score would go up by about N points").
- **Problem cards**, biggest first. Each card has a title, why it matters, what we found (the evidence), the points it's worth and a „Rezolvă” ("Fix") button.
- **„Rezolvate · N”** ("Solved · N"): what the business already does well, e.g. „Numărul de telefon e afișat” ("Your phone number is shown").
- **„Nu am putut verifica”** ("We couldn't check"): checks that couldn't run, each with the reason. These never count against the score.
- When everything in a chapter is solved, the chapter shows a "you're done here" state.

### Screen 4 · Fixing a problem (Rezolvare)

The fix opens in a side panel on desktop or a bottom sheet on a phone. There are four kinds (see §6.5): generated text, info page, developer instructions and step-by-step guide. Every panel ends with **„Am rezolvat”** ("Done"). The chapter score animates up at once, a toast shows the points gained, and the sidebar's problem count drops.

### Screen 5 · Visibility in Gemini (Vizibilitate în Gemini)

- The Gemini score and „Apari în X din 12 răspunsuri”.
- The 12 questions in three groups:
  - **General**: „Întrebări despre tot orașul” (questions about the whole city), e.g. „cea mai bună cafenea de specialitate din bucurești” ("the best specialty café in Bucharest").
  - **Cartier** (Neighbourhood): „Întrebări despre zona ta” (questions about your area), e.g. „cafenea de specialitate în domenii”.
  - **Situații** (Situations): „Ce caută oamenii, nu unde” (what people want, not where), e.g. „cafenea unde pot veni cu câinele” ("a café where I can bring my dog").
- For each question: whether you appeared, how many of the 3 runs named you, who Gemini recommended instead, an excerpt of its answer, and the Google Maps places it used as sources („Surse: Google Maps”).
- **„De ce îi alege Gemini pe ei?”** ("Why does Gemini choose them?"): a side-by-side table of you and the top 3 rivals (reviews, rating, photos, full opening hours), plain-language conclusions, and buttons that jump straight to the matching fix.
- **„Testează din nou”** ("Test again") reruns only the Gemini test, in under a minute.

### Screen 6 · Conversations (Conversații) with the assistant

- A list of conversations, including the setup chat, saved as „Configurare”.
- „Conversație nouă” ("New conversation") opens a chat with suggestions such as:
  - „Am adăugat programul de sărbători, marchează-l ca rezolvat” ("I added the holiday hours, mark it as done")
  - „Scrie-mi o postare pentru Profilul Google” ("Write me a post for my Google profile")
  - „De ce nu apar la „cafenea unde pot lucra cu laptopul”?” ("Why don't I show up for 'café where I can work on my laptop'?")
  - „Ce fac prima dată azi?” ("What should I do first today?")
- The owner says „Am răspuns la recenziile de pe Google” ("I replied to the reviews on Google"). The assistant finds the matching problem and offers to mark it with buttons such as „Da, marchează-l” ("Yes, mark it") / „Nu încă” ("Not yet"). When several problems match, it offers to mark all of them or just one.
- Nothing changes until the owner confirms. Then the scores rise, the assistant says by how much and suggests the next step. **„Anulează”** ("Undo") reverts it.
- The chapter's score card stays beside the chat.

### Navigation

- **Desktop:** a sidebar with the business card, the dashboard, Visibility in Gemini (with "5/12"), Conversations, and the 8 chapters, each with its count of open problems.
- **Phone:** a bottom tab bar: Acasă (Home), Gemini, Capitole (Chapters), Asistent (Assistant).

---

## 6. Features in detail

### 6.1 Conversational setup, led by Gemini

- Free text in, structured profile out. One answer can fill several fields.
- The backend checks every value Gemini extracts, so a bad guess can't slip into the scan.
- It works for businesses at any stage: no website, no Google profile, no Instagram all lead to a report with the right first steps (e.g. „Creează-ți Profilul Google”, "Create your Google profile").
- „Nu știu” is a valid answer to the questions about the Google profile and posts. It marks that check as "couldn't check", not as failed.

### 6.2 The live Gemini test: the core of the product

- **12 questions written the way customers ask them,** in Romanian with diacritics, built from the business type, city, neighbourhood and its attributes (terrace, card payments, dogs allowed…). They **never contain the business's name.**
- **Each question is asked 3 times** (36 answers), because AI answers vary. A question counts as "you appear" when at least 2 of the 3 answers name you.
- **The measurement is clean:** Gemini gets only the customer's question, grounded in Google Maps at the business's location. There's no system prompt and no hint about the business, so the answers are what a real customer would get.
- **Proof on screen:** every answer shows the Google Maps places Gemini used as sources.
- **Score:** how often you're mentioned (70 points), how high you're listed (15), and whether what Gemini says about you (hours, address) is correct (15).
- **Competitors:** the businesses Gemini names most often instead of you, with their reviews, rating, photos and hours side by side with yours.

### 6.3 The 8 chapters (47 checks)

| Chapter (in the app) | In English | What it checks | Weight in the overall score |
| --- | --- | --- | --- |
| Profilul Google | Google profile | Profile exists and is open, right category, full weekly hours, holiday hours, at least 5 photos, website link, phone, owner description, a post in the last 30 days, key attributes (terrace, card payments…), price range, profile claimed | 20% |
| Recenzii | Reviews | Number of reviews compared with nearby rivals, average rating, how recent the newest reviews are, share of reviews with an owner reply, reviews on a second platform (TripAdvisor, Booking or Booksy, by type) | 15% |
| Conținutul site-ului | Website content | Name and what you do on the homepage, address and neighbourhood, hours matching Google, phone, menu and prices as text (not a PDF or photo), a page per main service, answers to common questions (Wi-Fi, parking, pets, reservations), Romanian content | 15% |
| Site-ul, văzut de Gemini | The website, as Gemini sees it | HTTPS, Google and AI crawlers allowed in robots.txt, content readable without JavaScript, sitemap, business data in structured form (LocalBusiness), mobile speed, mobile layout, one page with all the basics | 10% |
| Aceleași informații peste tot | Same information everywhere | Present on the platforms expected for the type (Instagram, TripAdvisor, delivery apps…); name, address, phone and hours on those platforms match Google | 10% |
| Mențiuni pe alte site-uri | Mentions on other sites | How many other sites mention you, whether you're in a "best of" list, local press, forum and community mentions | 10% |
| Rețele sociale | Social media | Instagram profile exists, a post in the last 30 days, website, Instagram and Google profile link to each other, the Instagram bio says what you do and where | 5% |
| Te cunoaște deja Gemini? | Does Gemini already know you? | Asked without internet search: does Gemini know you exist, does it know your type and area, does it say anything wrong? This chapter has no direct fixes; it „Crește pe măsură ce rezolvi restul” ("grows as you fix the rest") | 5% |
| *Vizibilitate în Gemini* | *Visibility in Gemini* | *The live test in §6.2 (its own screen, not a chapter)* | *10%* |

### 6.4 Problems you can act on

- **Plain Romanian, no jargon.** For example: „Site-ul nu îi spune lui Gemini programul și adresa „pe limba lui”” ("Your website doesn't tell Gemini your hours and address 'in its own language'") instead of "Missing LocalBusiness JSON-LD".
- **Problems show what we found:** „Ai 452 de recenzii, iar cafenelele din jur au în jur de 3504” ("You have 452 reviews; the cafés around you have about 3,504"), „Am găsit răspuns la 0 din 5 întrebări obișnuite” ("We found answers to 0 of 5 common questions"), or your current Instagram bio, quoted.
- **Every problem shows its value:** "+N" is how much the chapter score rises when it's fixed. The dashboard ranks everything by how much it lifts the **overall** score.
- **Only real mismatches count.** "Str." and "Strada" are the same street, and "0721…" and "+40 721…" are the same phone number. Small formatting differences never become a problem card.

### 6.5 Four kinds of fix

| Fix type | What the owner gets | Used for, e.g. |
| --- | --- | --- |
| **Generated text** | A ready text in three tones: „Prietenos” (Friendly), „Profesionist” (Professional), „Scurt” (Short). It respects the character limit (150 for an Instagram bio) and says what it included („Am inclus: cartierul, ce servești, programul”, "Included: the neighbourhood, what you serve, the hours"). „Generează din nou” ("Generate again") writes a new one. „Copiază și deschide Instagram” copies the text and opens the right place, with the path shown („Profil › Editează profilul › Biografie”). | Instagram bio, Google description, Google post ideas, owner replies to reviews, website texts (address and area, menu, FAQ), a pitch email to local press |
| **Info page** | A complete "about us" page written from the business's real data: what it is, address and area, weekly and holiday hours, phone, Instagram, „Ne găsești și pe” ("Find us on"), menu and FAQ. Fields only the owner can know are highlighted in yellow („de completat”, "to fill in"). It can be downloaded as HTML or sent with „Trimite persoanei care îți face site-ul” ("Send to the person who makes your website") by WhatsApp or e-mail, with the message pre-written. | Businesses whose basics are scattered or missing online; with no website at all, it doubles as a simple site |
| **Developer instructions** | One document for the web person. For each technical problem: what's wrong, the evidence, the exact fix (robots.txt lines, a structured-data snippet already filled in with the business's details, "serve the menu as text, not a PDF"), and how to verify it. It can be sent by WhatsApp or e-mail or downloaded. | Crawler access, structured data, sitemap, speed, content hidden behind JavaScript |
| **Step-by-step guide** | Numbered steps plus a direct link to the right place (e.g. your Google profile) | Photos, hours, category, attributes, collecting more reviews, getting into "best of" lists |

### 6.6 „Am rezolvat”: instant progress

- One tap and the score updates at once: the ring animates, a toast shows "+X puncte", and the problem moves to „Rezolvate”.
- It's taken on trust for now and confirmed by the next scan, since changes on Google can take days to show up.

### 6.7 The assistant

- Understands what the owner did, in their own words, and proposes which problems to mark. Nothing changes until the owner confirms, and everything can be undone.
- Answers "what should I do next?" with the open problem worth the most.
- Writes texts on request, with the same generator as the fix panels.
- Reads the current report, so its answers are about this business's real numbers.

### 6.8 Checking again

- **„Testează din nou”** reruns only the Gemini test, in under a minute, after the owner changes something.
- **„Analizează din nou”** runs the whole analysis again with the same answers.

### 6.9 Honest by design

- **Code decides the score, not AI.** Fetching, comparing and scoring are deterministic code, so the same business always gets the same score. AI only reads messy pages, judges a few fuzzy things (does the category fit?), and writes texts.
- **"Couldn't check" is never "failed".** If a source is down or blocked, that check is left out of the score and shown with its reason.
- **Partial results are fine.** Each source is checked independently, so one slow website doesn't block the report.

---

## 7. User stories

### Getting started

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 1 | business owner | describe my business in my own words | I don't have to fill in a long form | Gemini-led chat that takes several facts from one answer and asks only what's missing |
| 2 | business owner | have the app find my Google profile | I don't have to know what a place ID is | Google Maps matches as cards with „Asta sunt eu”, or paste a Maps link |
| 3 | owner without a website, Google profile or Instagram | still get a useful report | the tool helps me at any stage | „Fără site” / „Fără profil Google” / „Fără rețele” chips; the report starts with creating what's missing |
| 4 | business owner | answer "I don't know" | I'm not penalised for what I don't know | „Nu știu” marks the check as "couldn't check", outside the score |

### Seeing where I stand

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 5 | business owner | see what's happening while it analyses | I trust it and don't leave | Five live steps with what was found ("Found 38 reviews") |
| 6 | business owner | get one number for how visible I am | I can track my progress | Overall score 0–100, coloured ring, one-line verdict |
| 7 | business owner | know whether Gemini actually recommends me | I know whether I have a problem at all | 12 customer questions × 3 runs: „Apari în X din 12 răspunsuri” |
| 8 | business owner | see who Gemini recommends instead of me | I know who I'm losing customers to | The top 3 competitors and how many answers name them |
| 9 | sceptical owner | read the real questions, answers and sources | I can see it's real and not made up | Every question with Gemini's answer excerpt and its Google Maps sources |
| 10 | business owner | understand why Gemini picks my competitors | I know what to change | „De ce îi alege Gemini pe ei?”: side-by-side numbers, conclusions, links to fixes |

### Knowing what to fix first

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 11 | busy owner | see the 3 things that matter most | I start where it counts | „Următorii pași”, ranked by effect on the overall score |
| 12 | business owner | see problems grouped into simple areas | I'm not overwhelmed | 8 chapters, each with its own score, intro and „Unde se rezolvă” |
| 13 | business owner | read each problem in plain words, with proof | I believe it and know why it matters | Title, why it matters, what we found, points |
| 14 | business owner | see what I already do well | I stay motivated | „Rezolvate · N” list in every chapter |
| 15 | business owner | know what couldn't be checked | I'm not misled | „Nu am putut verifica” with the reason, left out of the score |

### Fixing

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 16 | business owner | have the text written for me | I just copy and paste it | Generated text in 3 tones, within the character limit, with „Copiază și deschide …” |
| 17 | owner with a basic or no website | get a ready info page | Gemini finds my basics in one place | Generated page, yellow fields to fill in, HTML download |
| 18 | non-technical owner | send technical fixes to my web person in one tap | I don't have to understand robots.txt | Developer instructions sent by WhatsApp or e-mail, with evidence and how to verify |
| 19 | business owner | get step-by-step instructions with a direct link | I find the right button in Google Maps | Numbered steps, deep link, the path in the app |
| 20 | business owner | see my score rise as soon as I fix something | I feel progress | „Am rezolvat” → ring animates, "+X puncte" toast |

### Working with the assistant

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 21 | business owner | tell the assistant what I did, in my own words | my report updates without hunting for the right card | It proposes what to mark; I confirm; scores rise; „Anulează” undoes it |
| 22 | business owner | ask "what do I do today?" | I always have a next step | It answers with the open problem worth the most |
| 23 | business owner | ask it to write something (e.g. a Google post) | I get help beyond the fix panels | Same text generator as the panels |
| 24 | business owner | find my past conversations, including setup | I can pick up where I left off | „Conversații” list, setup saved as „Configurare” |

### Checking again

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 25 | business owner | re-run the Gemini test after my changes | I see whether Gemini now recommends me | „Testează din nou”, under a minute |
| 26 | business owner | re-run the full analysis | the whole report reflects my changes | „Analizează din nou” with the same answers |

### The web developer

| # | As a… | I want to… | So that… | How the product does it |
| --- | --- | --- | --- | --- |
| 27 | the owner's web developer | get exact, copy-paste fixes with evidence and a way to check them | I can fix it in minutes without a meeting | One document: what's wrong, evidence, exact fix (robots.txt lines, filled-in structured data), how to verify |

---

## 8. The demo case: Cafetăria Miciurin

**Cafetăria Miciurin – Specialty Coffee Shop** is a specialty café at Bulevardul Ion Mihalache 111, Domenii (Sector 1), București, one of the six shops of the Cafetăria chain. Its website is the chain's (cafetaria.ro), and it has no Instagram or TikTok. The numbers come from a real scan recorded on 15 November 2026.

### The headline

> **Cafetăria Miciurin has a perfect 5.0 rating from 452 reviews, as good as the cafés Gemini recommends instead. Yet Gemini names it in just 1 of 12 answers. Asked for „cafenea de specialitate în domenii” ("specialty café in Domenii"), exactly what it is and exactly where it is, Gemini recommends three other cafés.**

| | Google reviews | Rating | How many of the 12 questions name it |
| --- | --- | --- | --- |
| **Cafetăria Miciurin** | **452** | **5.0** | **1** |
| Saint Roastery Victoriei | 1,905 | 4.8 | 6 |
| Mad Goat | 567 | 4.9 | 6 |
| MABO ONE – Specialty Coffee Shop | 403 | 4.9 | 5 |

### Scores

- **Overall: 51 / 100.** „Ești pe drumul bun. Câteva lucruri simple te pot aduce mai sus.” ("You're on the right track. A few simple things can take you higher.")
- **Gemini visibility: 22.** Cafetăria Miciurin appears in 1 of 12 answers:
  - General (whole city): 0 of 4
  - Cartier (its own neighbourhood): 1 of 4
  - Situații (situations): 0 of 4
- For „cafenea de specialitate în domenii”, Gemini recommended KUMO Specialty Coffee, Onest Coffee and Dose Specialty Coffee.
- It isn't named for „cafenea unde pot veni cu câinele” ("a café where I can bring my dog") either, although Google lists it as dog-friendly.
- **„Te cunoaște deja Gemini?”: 100.** Gemini knows the café exists and what it is. It just doesn't recommend it.

| Chapter | Score |
| --- | --- |
| Profilul Google | 83 |
| Recenzii | 45 |
| Conținutul site-ului | 40 |
| Site-ul, văzut de Gemini | 75 |
| Aceleași informații peste tot | 0 |
| Mențiuni pe alte site-uri | 55 |
| Rețele sociale | 22 |
| Te cunoaște deja Gemini? | 100 |

### What the scan found (20 open problems)

- **Google profile:** no owner description and no post in the last 30 days. Everything else is complete: category, hours, photos, attributes and price.
- **Reviews:**
  - 20 of the last 20 reviews have no owner reply.
  - No reviews on TripAdvisor.
  - Fewer reviews than the most popular cafés nearby.
- **Website, which is the chain's:**
  - The homepage doesn't say clearly what this shop is.
  - The shop's address, neighbourhood, hours and phone aren't on it.
  - There are no prices next to the products, and the site answers none of 5 common customer questions.
  - There's no structured business data, no sitemap and no single page with the basics.
- **No Instagram.** Going by the demo's setup answers, it's also not on TripAdvisor, Glovo, Wolt or Bolt Food.
- **Mentions:** four coffee sites mention it (beanpassport.ro, europeancoffeetrip.com, mycoffee.guide, brewtifi.com), and it's in at least one "best of" list. There's no local press and no forum discussion.
- **What's already fine:**
  - Gemini knows it (100).
  - It has a 5.0 rating and new reviews this month.
  - The Google profile is otherwise complete.
  - The site loads fast on a phone and Google and AI crawlers can read it.

### What fixing it would do

- The three „Următorii pași” are:
  - getting on Instagram and the platforms expected for a café (+100 in „Aceleași informații peste tot”);
  - collecting more reviews (+30 in „Recenzii”);
  - creating the Instagram profile (+56 in „Rețele sociale”).
- On paper, fixing all 20 open problems would take Cafetăria Miciurin from **51 to about 92**, before counting any gain in the Gemini test itself.
- In the demo, generating the Google description and pressing „Am rezolvat” takes Profilul Google from **83 to 94**. Telling the assistant the reviews are answered raises „Recenzii”.

### The 5-minute demo path

1. **Setup:** type „Cafetăria Miciurin, o cafenea de specialitate în Domenii, București” and watch the card fill in. Confirm the website and the Google card, tap a few chips, and say there's no Instagram or TikTok.
2. **Analysis:** five steps tick off.
3. **Dashboard:** 51, „Apari în 1 din 12 răspunsuri” and the three cafés Gemini recommends instead.
4. **Visibility in Gemini:** open „cafenea de specialitate în domenii”, where Cafetăria Miciurin is missing, with the Google Maps sources. Then show „De ce îi alege Gemini pe ei?”.
5. **Generated fix:** generate the Google description in the „Profesionist” tone and press „Am rezolvat”: 83 → 94.
6. **Info page:** the chain's site doesn't show this shop's details, so here's a ready page with them and a yellow field to fill in. Then „Trimite persoanei care îți face site-ul”.
7. **Assistant:** „Am răspuns la recenziile de pe Google” → „Da, marchează-l” → the score rises → it suggests the next step. Show „Anulează”.
8. **Optional, WhatsApp:** turn on reply suggestions and press „Simulează o recenzie nouă”: the presenter's phone gets the café's newest real review with a reply ready to copy.

Optional bonus: a live scan of a judge's business.

---

## 9. Why it's different

- **It measures, it doesn't guess.** We ask Gemini the questions real customers ask, 36 times, and show the answers and their sources. Most tools only check a list of SEO rules.
- **It's built for owners, not marketers.** Everything is in plain Romanian, ranked by what matters most, with the text already written.
- **It does the work.** The output is a ready bio, a ready page, or a ready message to the web developer, not a list of advice.
- **It's fair and repeatable.** Scores come from fixed rules in code, never from AI, so the same business always gets the same score. Each check keeps its evidence (what we found, where, and what we expected). "Couldn't check" never counts against you.
- **It's fast.** A full real scan of Cafetăria Miciurin took 29 seconds.
- **It's local.** It's built around Romanian addresses, phone formats, neighbourhoods and the platforms people use here (Glovo, Wolt, Bolt Food, Booksy…).

---

## 10. Under the hood (for Q&A)

### Data sources

| What | Where it comes from |
| --- | --- |
| Google profile: category, hours, photos, phone, website, attributes, rating, reviews | Google Places API |
| Review dates and owner replies | SerpApi (Google Maps reviews) |
| Website text, robots.txt, sitemap, structured data | Fetched directly, the way AI crawlers see it; a real browser only for pages that come back empty |
| Mobile speed | Google PageSpeed Insights |
| Instagram bio, website, latest posts | Instagram Graph API (Business Discovery) |
| Mentions on other sites | Gemini with Google Search grounding |
| What Gemini recommends | Gemini with Google Maps grounding, at the business's location |
| What Gemini already knows | Gemini with no internet access |
| Nearby rivals | Google Places nearby search |

### Tech

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS. Designed for desktop and phone.
- **Backend:** Python, FastAPI, SQLite.
- **AI:** Gemini 3.5 Flash-Lite, through the Gemini API and Vertex AI for grounded calls.
- Built by **2 developers in under 24 hours**, working in parallel with Claude Code.

### Scoring, in one paragraph

Each check earns points; each chapter is worth 100. A chapter's score is the share of points earned over the checks that could run. The overall score is a weighted average of the 8 chapters and the Gemini test (weights in §6.3). A problem's "+N" is the chapter points it adds; the dashboard ranks problems by points × chapter weight, i.e. their effect on the overall score.

---

## 11. What v1 doesn't do (honest scope)

- **Runs on one laptop.** No accounts, no login, no hosting yet; one business at a time.
- **Gemini only.** No ChatGPT, Perplexity or others yet.
- **Tested through the Gemini API with Google Maps grounding.** That's a close stand-in for the Gemini app, not the app itself, so the product says "tested with Gemini".
- **Romanian only.**
- **Some Google profile details are self-reported:** the owner description, recent posts and whether the profile is claimed. Google doesn't expose them publicly without the owner connecting their account.
- **Instagram:** only business and creator accounts can be read. TikTok is checked as a link only. No Facebook.
- **Reviews:** Google only. Other platforms are asked about, not read.
- **Mentions:** found by site and title only. The pages aren't read and there are no dates.
- **Holiday hours:** Google shows them only for the coming 7 days, so they often can't be checked ahead.
- **„Am rezolvat” is on trust** until the next scan confirms it.
- **No automatic weekly re-scan** yet. It was designed, then cut from v1.

---

## 12. Where it could go next

These ideas are already named in the project's docs as "later" or "not in v1". They aren't commitments.

- **„Conectează profilul Google” ("Connect your Google profile"):** read the description, posts and replies directly instead of asking.
- **Automatic weekly check** with progress over time.
- **More AI assistants** (ChatGPT first) and more platforms (Tripadvisor data, Apple Maps, Bing, Romanian directories, Facebook).
- **Several businesses per account** (the business switcher is already in the design).
- **Mention dates**, to tell fresh press from old.

---

## 13. Still to decide before the pitch

The project doesn't cover these, so they need your input:

- **Business model and pricing.**
- **Market numbers** (how many local businesses, how many people ask AI for recommendations) with sources.
- **Team slide.**
- **Whether to offer a live scan** of a judge's business. It needs the demo laptop and an internet connection; the recorded Cafetăria Miciurin scan is the fallback.
