# Data Collection Algorithm — Skeleton

*How the system collects, checks and scores everything about a business. Compiled 14 November 2026.*

Sample business used in examples: **Cafeneaua Boema**, specialty café, Cotroceni, București.

---

## 0. Overview

```
Onboarding answers
      │
      ▼
[1] Find the business on Google (place ID)
      │
      ▼
[2] Build the canonical profile (Google data = source of truth)
      │
      ▼
[3] Run collectors in parallel ───────────────────────────────┐
      ├─ 3.1 Google profile          → Profilul Google         │
      ├─ 3.2 Reviews                 → Recenzii                │
      ├─ 3.3 Website                 → Conținutul site-ului    │
      │                                 + Site-ul, văzut de Gemini
      ├─ 3.4 Listings & platforms    → Aceleași informații peste tot
      ├─ 3.5 Mentions on the web     → Mențiuni pe alte site-uri
      ├─ 3.6 Social media            → Rețele sociale          │
      ├─ 3.7 Training-data probe     → Te cunoaște deja Gemini?│
      ├─ 3.8 Live Gemini test        → Vizibilitate în Gemini  │
      └─ 3.9 Competitors             → comparison card (Screen 5)
      │                                                        │
      ▼                                                        │
[4] Normalize & cross-check (addresses, phones, hours) ◄───────┘
      │
      ▼
[5] Score every check → chapter scores → overall score
      │
      ▼
[6] Turn failed checks into problems + fixes
      │
      ▼
[7] Assemble report, cache, allow re-test
```

### Design principles

1. **Code decides, the LLM reads and writes.** Fetching, comparing and scoring are deterministic code, so the same business always gets the same score. The LLM is only used to extract facts from messy pages, generate test prompts, parse AI answers and write fix texts.
2. **Every check stores its evidence.** The URL, the value found and the expected value, so each problem card can explain itself.
3. **Unknown is not a fail.** If a check can't run (timeout, blocked page), mark it `unknown`, leave it out of the score and show "Nu am putut verifica".
4. **Google is the source of truth.** All other sources are compared against the Google profile, since Gemini reads it directly.
5. **Partial results are fine.** Each collector runs independently, with its own timeout. The report shows what finished.
6. **The measured Gemini stays clean.** Live-test calls send only the customer's question with Maps and Search grounding: no system prompt, no business context. Otherwise the test measures our prompt, not what a real customer gets.

---

## 1. Inputs (from onboarding, Screen 1)

| Field | Example | Required | Used by |
|---|---|---|---|
| `business_name` | Cafeneaua Boema | yes | all |
| `business_type` | Cafenea | yes | categories, prompts, competitors |
| `city`, `neighborhood` | București, Cotroceni | yes | search, prompts, location bias |
| `has_website`, `website_url` | da, https://… | yes / if da | 3.3 |
| `google_maps_url` *or* picked candidate | maps.app.goo.gl/… | yes (or "nu am profil") | 1 |
| `facebook_url`, `instagram_url`, `tiktok_url` | … | skippable | 3.4, 3.6 |
| `platforms[]` (+ URLs if known) | TripAdvisor, Glovo, Booksy | skippable | 3.2, 3.4 |

Optional self-reported answers (to cover data no API gives us; see §9):
- "Ai o descriere în profilul Google?" (da / nu / nu știu)
- "Când ai postat ultima dată pe Google / Instagram / Facebook?"

---

## 2. Data model

```jsonc
Business {
  id, name, type, city, neighborhood,
  inputs: { website_url, maps_url, socials: {...}, platforms: [...] },
  place_id,               // Google place ID, set in step 1
  canonical: CanonicalProfile,
  sources: [SourceSnapshot],
  checks: [CheckResult],
  problems: [Problem],
  scores: { chapters: {chapter_id: 0-100}, gemini: 0-100, overall: 0-100 },
  live_test: LiveTestResult,
  competitors: [CompetitorSnapshot],
  scanned_at
}

CanonicalProfile {          // normalized, from Google
  name, address: NormalizedAddress, phone: "+40…",
  website, hours: WeeklyHours, special_hours, category,
  rating, review_count, photo_count, attributes: {...}, location: {lat, lng}
}

SourceSnapshot {            // one per page/platform we read
  source: "website" | "facebook" | "tripadvisor" | "glovo" | ...,
  url, fetched_at, status: "ok" | "blocked" | "not_found" | "error",
  raw_text_excerpt, extracted: { name, address, phone, hours, ... }
}

CheckResult {
  check_id: "G04", chapter_id: "google_profile",
  status: "pass" | "partial" | "fail" | "unknown",
  points_earned, points_max,
  evidence: { found, expected, url }
}

Problem {
  check_id, chapter_id, title_ro, why_ro,      // plain Romanian, no jargon
  points, impact,                               // impact = points × chapter weight
  fix_type: "generate" | "owner_action" | "dev_export",
  fix_payload                                   // generated text, steps, or dev instructions
}
```

---

## 3. Pipeline

### Step 1 — Find the business on Google (entity resolution)

**Goal:** get the Google **place ID**. Every later step keys off it.

```
if maps_url given:
    follow redirects (maps.app.goo.gl → full Maps URL)
    parse name + coordinates from the URL
    Places Text Search(textQuery = name, locationBias = circle(coords, 200 m))
    pick the top result whose name matches (fuzzy, diacritics-insensitive)
elif owner pressed "Caută-mă pe Google":
    Places Text Search(textQuery = f"{name} {neighborhood} {city}",
                       locationBias = circle(neighborhood_center, 3 km))
    show top 5 candidates (name, address, photo) → owner picks one
else ("nu am profil Google"):
    place_id = null → chapter "Profilul Google" scores 0,
    top fix = "Creează-ți profilul Google"
```

Error state: link can't be resolved → "Nu am putut citi linkul" + retry or switch to search.

### Step 2 — Build the canonical profile

Call **Place Details (New)** with a field mask. Fields to request:

| Purpose | Fields |
|---|---|
| Identity | `id`, `displayName`, `primaryType`, `primaryTypeDisplayName`, `types`, `businessStatus`, `googleMapsUri` |
| Contact | `formattedAddress`, `addressComponents`, `location`, `nationalPhoneNumber`, `internationalPhoneNumber`, `websiteUri` |
| Hours | `regularOpeningHours`, `currentOpeningHours` (special days) |
| Reputation | `rating`, `userRatingCount`, `reviews` (max 5, sorted by relevance) |
| Media & details | `photos` (max 10 returned), `editorialSummary`, `priceLevel`, `priceRange` |
| Attributes | `dineIn`, `takeout`, `delivery`, `outdoorSeating`, `servesCoffee`, `servesBreakfast`, `allowsDogs`, `goodForGroups`, `paymentOptions`, `accessibilityOptions` |

Normalize everything (§4) and save as `canonical`. Emit progress tick **"Google"**.

### Step 3 — Collectors (run in parallel)

Each collector: `async collect(business) → [SourceSnapshot], [CheckResult]`, with its own timeout (15–30 s).

#### 3.1 Google profile → *Profilul Google*

Pure code on the canonical profile, plus one LLM call to judge the category.

```
checks:
  G01 profile exists and businessStatus == OPERATIONAL     (gate)
  G02 primary category fits the business                   LLM judge: business_type + website facts vs primaryType
  G03 regular hours set for all 7 days                     regularOpeningHours
  G04 special/holiday hours set                            currentOpeningHours special days (verify coverage)
  G05 at least 5 photos                                    len(photos)  (API caps at 10)
  G06 website link set                                     websiteUri
  G07 phone set                                            nationalPhoneNumber
  G08 owner description present                            self-report (not in Places API)
  G09 post in last 30 days                                 self-report (Business Profile API only)
  G10 key attributes filled for the type                   attribute fields relevant to business_type
  G11 price level/range set                                priceLevel / priceRange
```

#### 3.2 Reviews → *Recenzii*

```
google = canonical.rating, canonical.review_count, canonical.reviews[≤5]
competitor_median = median(review_count of top 3 competitors)   # from 3.9

checks:
  R01 review count vs competitor median     scaled: ≥ median → full, ≥ 50% → half
  R02 rating                                ≥ 4.6 full, 4.3–4.5 partial, < 4.3 fail
  R03 recency                               newest of the 5 returned reviews: ≤ 30 days full, ≤ 90 partial
                                            (approximation: only 5 reviews visible, see §9)
  R04 owner replies to reviews              Business Profile API only → self-report or unknown for demo
  R05 reviews on a second relevant platform TripAdvisor (cafés, restaurants), Booking (hotels), Booksy (salons)
```

For other platforms: fetch the listing page (§3.4 fetch routine), LLM extracts `{rating, review_count, newest_review_date}`.
Emit tick **"recenzii"**.

#### 3.3 Website → *Conținutul site-ului* + *Site-ul, văzut de Gemini*

```
if not has_website:
    both chapters → 0; top fix "Fă-ți un site simplu" (offer the generated info page)
    return

pages = [homepage] + up to 3 internal pages (from sitemap.xml or nav links:
        menu, contact, about, services, FAQ)

for each page:
    raw = HTTP GET with httpx, no JavaScript          (what non-Google AI crawlers see)
    if looks_empty(raw):                              # very little visible text, OR no business name/address
                                                      # from the Google profile, OR an empty SPA shell
                                                      # (<div id="root"></div>, "enable JavaScript" notice)
        rendered = Playwright render                  # lazy-launched, reused, 15 s limit per page
                                                      # (what people and Google see)
    text = rendered if rendered else raw
    store raw text, rendered text (if any), and which one was used

robots   = fetch /robots.txt, parse per user agent
sitemap  = fetch /sitemap.xml (or Sitemap: line in robots.txt)
jsonld   = parse <script type="application/ld+json"> blocks
facts    = LLM extract(text of all pages) → WebsiteFacts JSON:
           { name, what_it_is, address, neighborhood, phone, hours,
             menu_items_or_services, prices_present, faq_items, language }
```

Checks — **Conținutul site-ului** (on `facts`, compared with canonical):

```
  C01 name + what the business is, visible on homepage (title / H1 / first text)
  C02 address + neighborhood in page text
  C03 hours in page text, matching Google
  C04 phone in page text
  C05 menu / products / prices as text (not only PDF or image)
  C06 a page or section per main service/category
  C07 answers to common questions (FAQ: laptop, Wi-Fi, parking, pets, reservations)
  C08 content in Romanian
```

Checks — **Site-ul, văzut de Gemini** (technical, all go to the developer export):

```
  T01 site reachable, HTTPS, status 200
  T02 robots.txt allows Googlebot and Google-Extended   (verify Google-Extended's effect on Gemini grounding)
  T03 robots.txt allows OAI-SearchBot, GPTBot, PerplexityBot, ClaudeBot
  T04 key content present in raw HTML                   name, address, hours (from Google) found in raw HTML;
                                                        fails if they only appear after the Playwright render
  T05 sitemap.xml exists and lists the main pages
  T06 LocalBusiness / CafeOrCoffeeShop JSON-LD present, matching NAP
  T07 acceptable speed                                   time to first byte, page weight
  T08 mobile viewport meta tag present

gate: if T01 fails, or T02 blocks Googlebot, or T04 finds an empty shell
      → cap "Conținutul site-ului" at 30 (Gemini can't read that content anyway)
```

Emit tick **"website"**.

#### 3.4 Listings & platforms → *Aceleași informații peste tot*

```
targets = owner-provided URLs
        + platforms expected for business_type
          (café: Facebook, Instagram, TripAdvisor, Glovo/Wolt/Bolt Food if delivery,
           salon: Booksy, hotel: Booking; Bing Places, Apple Maps, Romanian directories)

for each target without a URL:
    search f'"{name}" {neighborhood} {platform}'      (Gemini + Search grounding, or a SERP API)
    accept a result only if the page name + address match the canonical profile

for each URL:
    fetch (raw first; headless browser if the page is JS-heavy)
    LLM extract → { name, address, phone, hours }
    normalize (§4) and compare field by field with canonical

checks:
  L01 coverage: present on the expected platforms for the type      (30 pts)
  L02 consistency: matched fields / compared fields across sources  (70 pts)
      each mismatch → its own problem, e.g.
      "Telefonul de pe Glovo e diferit de cel de pe Google"
```

#### 3.5 Mentions on the web → *Mențiuni pe alte site-uri*

```
queries = [
  f'"{name}" {city}',
  f'"{name}" {neighborhood}',
  f'cele mai bune cafenele {neighborhood}',      # best-of lists
  f'top cafenele {city}',
  f'"{name}" recenzie',
]
results = run each query (Gemini + Google Search grounding → grounding chunks, or SERP API)

drop: own website, social profiles, listing platforms from 3.4

for each remaining page:
    fetch, LLM classify → { mentions_business: bool, type: news|blog|list|forum|other,
                            sentiment, published_date }

checks:
  M01 number of distinct third-party domains mentioning the business   0 / 1–2 / 3–5 / 6+
  M02 included in at least one best-of / top list for city or neighborhood
  M03 a local news or press mention
  M04 at least one mention in the last 12 months
  M05 a forum / community mention
```

#### 3.6 Social media → *Rețele sociale*

Social platforms block most scraping, so keep this light for the hackathon.

```
for each social URL:
    check it resolves (HTTP status, not a 404 or login wall)
    try to read public bio/description (og:description meta tags)
    LLM extract → { mentions_what, mentions_where, has_link }

checks:
  S01 Facebook page exists and resolves
  S02 Instagram profile exists and resolves
  S03 posted in last 30 days                     self-report (or page data if readable)
  S04 cross-links: website ↔ socials ↔ Google profile
  S05 bio says what + where + link/hours
```

Emit tick **"rețele sociale"**.

#### 3.7 Training-data probe → *Te cunoaște deja Gemini?*

```
Gemini API, NO tools (no Search, no Maps grounding):
  prompt: f"Ce știi despre {name} din {neighborhood}, {city}?"
          + f"Recomandă câteva cafenele din {neighborhood}."
LLM judge (separate call) compares the answer with canonical:

checks:
  K01 knows the business exists                 (50)
  K02 knows the correct type and neighborhood   (30)
  K03 states no wrong facts                     (20)

no direct fixes → card shows "Crește pe măsură ce rezolvi restul"
```

#### 3.8 Live Gemini test → *Vizibilitate în Gemini* (+ Screen 5)

```
1. Generate prompts (LLM, Romanian), 4 per group, 12 total:
   General   : "cea mai bună cafenea din București", ...
   Cartier   : "cafenea în Cotroceni", ...
   Situații  : built from extracted facts/attributes,
               e.g. "cafenea unde pot lucra cu laptopul în Cotroceni"
   (+ English variants for tourist-facing businesses)

2. Run each prompt 3 times:
   Gemini API with tools = [Grounding with Google Maps, Grounding with Google Search]
   no system prompt, no business context: only the customer's question
   location = neighborhood center lat/lng for Cartier and Situații prompts

3. Parse each answer:
   mentioned  = target place_id in groundingChunks[].maps.placeId
                OR fuzzy name match in text (diacritics-insensitive)
   position   = order of first appearance among businesses named in the text
   competitors= other place IDs / names in the answer
   facts_ok   = LLM judge: stated hours/address for the target vs canonical

4. Aggregate:
   prompt counts as "mentioned" if target appears in ≥ 2 of 3 runs
   → "Apari în X din 12 răspunsuri"
   top 3 competitors = most frequently mentioned other businesses
   store answers + sources per prompt for Screen 5

score:
  mention rate      (70)   X / 12, scaled
  average position  (15)   1st = full, 2nd–3rd = partial
  facts correct     (15)
```

Emit tick **"Gemini"**.

#### 3.9 Competitors → comparison card

```
candidates = top 3 from live test (3.8)
           ∪ Places Nearby Search(includedTypes for business_type,
                                  circle(business location, 1.5 km), rank by popularity)
for top 3: Place Details (same fields as Step 2)
comparison rows: review_count, rating, photo_count (capped at 10 → show "10+"),
                 hours complete (7 days + special hours), has website
```

### Step 4 — Normalize & cross-check

| Field | Rules |
|---|---|
| Address | lowercase; strip diacritics and unify ș/ş, ț/ţ; expand abbreviations (Str. → strada, Bd./Bdul → bulevardul, Nr. → numărul, Sect. → sector, Calea, Șos. → șoseaua); compare street + number + sector, ignore formatting |
| Phone | digits only; `07xx…`, `+407xx…`, `00407xx…` → `+407xx…` |
| Hours | parse into `{day: [(open, close)]}`; accept "L–V", "Luni–Vineri", "Mon–Fri", "non-stop" |
| Name | strip legal suffixes (SRL, S.R.L.), quotes, diacritics; fuzzy ratio ≥ 0.85 |

Only flag **real** mismatches (different number, street, phone digits or hours). "Str." vs "Strada" is the same address after normalization and should not become a problem card.

### Step 5 — Scoring

```
chapter_score = round(100 × Σ points_earned / Σ points_max)    # over checks that are not "unknown"
apply gates/caps (T-gate on Conținutul site-ului; no-website → 0; no Google profile → 0)

overall = Σ weight[ch] × chapter_score[ch]

weights:
  Profilul Google              0.20
  Recenzii                     0.15
  Conținutul site-ului         0.15
  Site-ul, văzut de Gemini     0.10
  Aceleași informații peste tot 0.10
  Mențiuni pe alte site-uri    0.10
  Rețele sociale               0.05
  Te cunoaște deja Gemini?     0.05
  Vizibilitate în Gemini       0.10
```

#### Check catalog (points per chapter = 100)

| Chapter | Check | Points | Data source | Fix type |
|---|---|---|---|---|
| Profilul Google | G02 category | 15 | Places + LLM | owner_action |
| | G03 regular hours | 15 | Places | owner_action |
| | G04 special hours | 10 | Places (verify) | owner_action |
| | G05 ≥ 5 photos | 15 | Places | owner_action |
| | G06 website link | 10 | Places | owner_action |
| | G07 phone | 10 | Places | owner_action |
| | G08 description | 10 | self-report | generate |
| | G09 recent post | 5 | self-report | generate |
| | G10 attributes | 5 | Places | owner_action |
| | G11 price range | 5 | Places | owner_action |
| Recenzii | R01 count vs competitors | 30 | Places | owner_action (review link/QR) |
| | R02 rating | 20 | Places | owner_action |
| | R03 recency | 25 | Places (5 reviews) | owner_action |
| | R04 owner replies | 15 | self-report | generate (reply drafts) |
| | R05 second platform | 10 | fetch + LLM | owner_action |
| Conținutul site-ului | C01 name + what | 15 | LLM extract | generate |
| | C02 address + area | 15 | LLM extract | generate |
| | C03 hours match | 15 | LLM extract | generate |
| | C04 phone | 10 | LLM extract | generate |
| | C05 menu as text | 15 | LLM extract | generate |
| | C06 page per service | 10 | LLM extract | dev_export |
| | C07 FAQ | 10 | LLM extract | generate |
| | C08 Romanian | 10 | LLM extract | generate |
| Site-ul, văzut de Gemini | T01 reachable/HTTPS | 15 | HTTP | dev_export |
| | T02 Google crawlers allowed | 20 | robots.txt | dev_export |
| | T03 other AI crawlers allowed | 10 | robots.txt | dev_export |
| | T04 content in raw HTML | 25 | raw HTML (+ Playwright fallback) | dev_export |
| | T05 sitemap | 10 | HTTP | dev_export |
| | T06 LocalBusiness JSON-LD | 10 | HTML parse | dev_export (generated snippet) |
| | T07 speed | 5 | HTTP timing | dev_export |
| | T08 mobile viewport | 5 | HTML parse | dev_export |
| Aceleași informații peste tot | L01 coverage | 30 | search + fetch | owner_action |
| | L02 consistency | 70 | fetch + LLM + §4 | owner_action |
| Mențiuni pe alte site-uri | M01 domains count | 40 | search + LLM | owner_action |
| | M02 best-of list | 25 | search + LLM | owner_action (outreach message) |
| | M03 local press | 15 | search + LLM | generate (pitch email) |
| | M04 recent mention | 10 | search + LLM | — |
| | M05 forum mention | 10 | search + LLM | — |
| Rețele sociale | S01 Facebook | 20 | HTTP | owner_action |
| | S02 Instagram | 20 | HTTP | owner_action |
| | S03 recent post | 25 | self-report | generate (post ideas) |
| | S04 cross-links | 15 | HTML + bios | owner_action |
| | S05 bio complete | 20 | og tags + LLM | generate |
| Te cunoaște deja Gemini? | K01–K03 | 50/30/20 | Gemini, no tools | — |
| Vizibilitate în Gemini | mention rate / position / facts | 70/15/15 | Gemini + grounding | — |

### Step 6 — Problems & fixes

```
for each check with status in (fail, partial):
    problem.points = points_max - points_earned          # shown as "+8" on the card
    problem.impact = problem.points × weight[chapter]    # used for sorting
    problem.title_ro, problem.why_ro = from a template per check_id
                                       (LLM only to personalize wording)
    problem.fix_type, fix_payload:
        generate     → LLM writes the text (description, Instagram bio, FAQ, review replies,
                       info page "Pagina ta de informații pentru Google")
        owner_action → short numbered steps, deep link where possible (Google profile, Instagram)
        dev_export   → technical instruction block, collected into one export

sort problems inside a chapter by points
"Începe de aici" = chapter with the highest Σ impact
```

**Developer export** (one document per business, Markdown/PDF, also sent as a pre-written message):

```
For each dev_export problem:
  - What's wrong (one line)
  - Evidence (URL, what we found)
  - Exact fix (e.g. robots.txt lines to change, JSON-LD snippet filled with the café's data,
    "serve the menu as HTML text, not a PDF")
  - How to verify (e.g. "curl -A 'GPTBot' https://… should return the menu text")
```

### Step 7 — Report, caching, re-test

```
report = { overall, chapters[], gemini_card, problems_by_chapter, competitors, live_test_answers }

"Am rezolvat" on a problem:
    mark as claimed_fixed, add the points provisionally (ring animates, toast "+X puncte")
    verify on the next scan; if still failing → move back with a note
    (Google changes can take days to show up)

"Testează din nou":
    rerun 3.8 (live test) + collectors for chapters with claimed fixes
    update "Ultima verificare: azi"

caching: store place IDs freely; check Google Maps Platform terms before caching other Places content
```

---

## 4. LLM calls (summary)

All with structured JSON output. Use a fast, cheap model for extraction; the same model is fine for generation in a hackathon.

| ID | Purpose | Input | Output |
|---|---|---|---|
| L1 | Category judge | business_type, website facts, primaryType | `{fits: bool, suggested_category}` |
| L2 | Website fact extraction | raw text of pages | `WebsiteFacts` |
| L3 | Listing extraction | listing page text | `{name, address, phone, hours, rating, review_count}` |
| L4 | Mention classification | page text + business name | `{mentions_business, type, sentiment, date}` |
| L5 | Live-test prompt generation | type, city, neighborhood, attributes | 12 prompts in 3 groups |
| L6 | Answer parsing (backup to grounding) | Gemini answer text | `{businesses_in_order[], stated_facts}` |
| L7 | Training-data judge | no-tools answer + canonical | `{knows, correct_type_area, wrong_facts[]}` |
| L8 | Fix generation | problem + canonical + tone | text (description, bio, FAQ, info page, dev instructions) |
| L9 | Problem wording | check template + business | `title_ro`, `why_ro` |

---

## 5. Orchestration skeleton

```python
async def analyze(inputs) -> Report:
    business = Business.from_inputs(inputs)

    business.place_id = await resolve_place(inputs)                 # Step 1
    emit("Google", "running")
    business.canonical = await build_canonical(business.place_id)   # Step 2
    emit("Google", "done")

    collectors = [                                                  # Step 3
        google_profile(business),        # 3.1
        reviews(business),               # 3.2  (needs competitors → await 3.9 inside)
        website(business),               # 3.3
        listings(business),              # 3.4
        mentions(business),              # 3.5
        social(business),                # 3.6
        training_probe(business),        # 3.7
        live_test(business),             # 3.8
        competitors(business),           # 3.9
    ]
    results = await gather_with_timeouts(collectors, per_task=30)    # failures → checks "unknown"

    business.sources, business.checks = merge(results)
    cross_check(business)                                           # Step 4
    business.scores = score(business.checks, WEIGHTS, GATES)        # Step 5
    business.problems = build_problems(business)                    # Step 6
    return assemble_report(business)                                # Step 7
```

Progress ticks for the loading screen ("Analizăm afacerea ta…"):

| Tick | Finishes when |
|---|---|
| Google | Steps 1–2 + 3.1 done |
| recenzii | 3.2 done |
| website | 3.3 done |
| rețele sociale | 3.4 + 3.6 done (consider adding a tick "alte site-uri" for 3.5) |
| Gemini | 3.7 + 3.8 done |

---

## 6. Error handling

| Situation | Behavior |
|---|---|
| Maps link can't be resolved | Error state "Nu am putut citi linkul" → retry or "Caută-mă pe Google" |
| No Google profile | Profilul Google = 0, top fix "Creează-ți profilul Google"; live test still runs |
| Website down / blocked | T01 fails, content checks `unknown`, dev export explains |
| Platform page blocks fetch | that source `unknown`, excluded from L02 denominator |
| Collector timeout | its checks `unknown`, card says "Nu am putut verifica" with retry |
| Gemini API error/rate limit | retry with backoff; if still failing, show live test as "în curs" and score without it (renormalize weights) |

---

## 7. Demo tips (hackathon)

- **Precompute a fixture for Cafeneaua Boema** (or a real café you choose) so the demo doesn't depend on live API latency. Keep the live path working for one "real" scan on stage.
- **Run the live test in the background** and show the other chapters first; it's the slowest step (12 prompts × 3 runs).
- **Show Gemini's sources** on Screen 5 from `groundingChunks`; it makes the result feel real.

---

## 8. Cost/latency estimate (rough)

| Step | Calls per scan |
|---|---|
| Places (Text Search + Details + competitors) | ~5–8 |
| Website fetches | ~4 raw; rendered only for pages that come back empty |
| Listing/mention fetches | ~10–20 |
| LLM extraction/classification | ~20–30 |
| Live test | 36 grounded Gemini calls |
| Training probe | 2 |

Target total time: under 90 seconds with parallel collectors.

---

## 9. Known limitations & open items

- **Places API limits:** returns max 5 reviews (by relevance, not date) and max 10 photos. Review recency is an approximation.
- **No owner description, posts or review replies via Places API.** These need the **Business Profile API**, which isn't public: access must be requested (reviewed within ~14 days) and every request needs the owner's OAuth consent. For the hackathon, use self-report; later, add "Conectează profilul Google".
- **Gemini API ≠ the consumer Gemini app.** The grounded API answers are a close proxy, not identical. Say "testat cu Gemini" rather than promising the exact app result.
- **Social platforms block scraping.** Keep social checks to existence, links and self-report.
- **Bing Places, Apple Maps, Romanian directories:** no easy API for the hackathon; check via search or leave for later. Build the directory list (open item).
- **To verify:** whether `currentOpeningHours` reliably exposes holiday hours; how `Google-Extended` affects Gemini grounding.
- **ChatGPT (later):** same live-test loop with OpenAI's API and its web search tool; add as a second engine behind the same scoring.

---

## Sources

- Places API (New) — Place resource (max 5 reviews, max 10 photos): https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places
- Places API (New) — Place Details: https://developers.google.com/maps/documentation/places/web-service/place-details
- Places API (New) — overview: https://developers.google.com/maps/documentation/places/web-service/op-overview
- Gemini API — Grounding with Google Maps: https://ai.google.dev/gemini-api/docs/maps-grounding
- Google Business Profile APIs — FAQ (access request, ~14-day review): https://developers.google.com/my-business/content/faq
- Google Business Profile APIs — OAuth overview: https://developers.google.com/my-business/content/oauth-overview
- Vercel — The rise of the AI crawler (AI crawlers don't run JavaScript): https://examples.vercel.com/blog/the-rise-of-the-ai-crawler
