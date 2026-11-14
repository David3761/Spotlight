# Data Collection Algorithm

*Final version · 14 November 2026. Merges the earlier algorithm skeleton with the data-retrieval resources list.*

How the system collects, checks and scores everything about a business. Dev B implements all of it except the fix texts (§6, Dev A). Response shapes are in [contract.md](contract.md).

Sample business used in examples: **Cafeneaua Boema**, specialty café, Cotroceni, București.

---

## 0. Overview

```
Onboarding answers (place_id already picked in the browser)
      │
      ▼
[1] Resolve the place ID (only if the frontend didn't send one)
      │
      ▼
[2] Build the canonical profile (Google = source of truth)
      │
      ├──► start 3.8 live test immediately (slowest step)
      ▼
[3] Run collectors in parallel ────────────────────────────────────┐
      ├─ 3.1 Google profile         → profil                       │
      ├─ 3.2 Reviews (+ SerpApi)    → recenzii                     │
      ├─ 3.3 Website (+ PageSpeed)  → continut + site              │
      ├─ 3.4 Listings               → info                         │
      ├─ 3.5 Mentions               → mentiuni                     │
      ├─ 3.6 Social (+ Meta)        → social                       │
      ├─ 3.7 Training-data probe    → cunoaste                     │
      ├─ 3.8 Live Gemini test       → gemini block                 │
      └─ 3.9 Competitors            → R01 median + Screen 5        │
      │                                                            │
      ▼                                                            │
[4] Normalize & cross-check (addresses, phones, hours) ◄───────────┘
      │
      ▼
[5] Score every check → chapter scores → overall score
      │
      ▼
[6] Turn failed checks into problems + fixes
      │
      ▼
[7] Assemble report, save, allow re-test
```

### Design principles

1. **Code decides, the LLM reads and writes.** Fetching, comparing and scoring are deterministic code, so the same business always gets the same score. The LLM only extracts facts from messy pages, generates test prompts, parses AI answers, judges a few fuzzy checks into booleans, and writes fix texts.
2. **Every check stores its evidence:** the URL, the value found and the expected value, so each problem card can explain itself.
3. **Unknown is not a fail.** If a check can't run (timeout, blocked page, no API access), mark it `unknown`, leave it out of the score and show „Nu am putut verifica”.
4. **Google is the source of truth.** Every other source is compared against the Google profile, since Gemini reads it directly.
5. **Partial results are fine.** Each collector runs independently with its own timeout; the report shows what finished.
6. **The measured Gemini stays clean.** Live-test calls send only the customer's question with Maps grounding: no system prompt, no business context.

---

## 1. Inputs (Screen 1)

The full shape is `ScanInputs` in [contract.md](contract.md).

| Field | Example | Required | Used by |
|---|---|---|---|
| `business_name` | Cafeneaua Boema | yes | all |
| `business_type` | `cafenea` | yes | categories, prompts, competitors, expected platforms |
| `city`, `neighborhood` | București, Cotroceni | yes | search, prompts, location |
| `has_website`, `website_url` | da, https://… | yes / if da | 3.3 |
| `place_id` (picked candidate or resolved link) or `no_google_profile` | ChIJ… | yes | 1, 2 |
| `instagram_url`, `tiktok_url` | … | skippable | 3.4, 3.6 |
| `platforms[]` | Glovo, Wolt | skippable | 3.2 (R05), 3.4 (L01) |
| `self_report.profile_claimed` | da / nu / nu știu | skippable | G12 |
| `self_report.has_google_description` | da / nu / nu știu | skippable | G08 |
| `self_report.last_google_post` | luna asta / mai demult / niciodată / nu știu | skippable | G09 |
| `self_report.last_social_post` | same | skippable | S03 fallback |

„Nu știu” or a skipped question makes the check `unknown`.

---

## 2. Internal data model

The report the frontend sees is in [contract.md](contract.md). Internally the pipeline keeps:

```jsonc
Business {
  id, inputs: ScanInputs,
  place_id, canonical: CanonicalProfile,
  website_facts: WebsiteFacts | null,
  sources: [SourceSnapshot],
  checks: [CheckResult],
  live_test: LiveTestResult,
  competitors: { nearby: [CompareRow], from_live_test: [CompareRow] },
  scanned_at
}

CanonicalProfile {            // normalized, from Place Details
  name, address: NormalizedAddress, phone: "+40…", website, google_maps_uri,
  hours: WeeklyHours, special_days, primary_type, types, business_status,
  rating, review_count, photo_count, attributes: {...}, price_level, price_range,
  location: {lat, lng}
}

SourceSnapshot {              // one per page/platform read
  source: "website" | "instagram" | "glovo" | ...,
  url, fetched_at, status: "ok" | "blocked" | "not_found" | "error",
  raw_text_excerpt, rendered: bool, extracted: { name, address, phone, hours, ... }
}

CheckResult {
  check_id: "G04", chapter_id: "profil",
  status: "pass" | "partial" | "fail" | "unknown",
  points_earned, points_max,
  claimed_fixed: bool,        // set by "Am rezolvat" / assistant confirm
  evidence: { found, expected, url }
}
```

---

## 3. Pipeline

### Step 1 — Resolve the place ID

The frontend normally sends `place_id` (picked from `/api/places/search` or `/api/places/resolve-link`). The same code backs those endpoints:

```
resolve-link(url):
    follow redirects (maps.app.goo.gl → full Maps URL)
    parse name + coordinates (or a place ID / CID) from the URL
    Places Text Search(textQuery = name, locationBias = circle(coords, 200 m))
    pick the top result whose name matches (rapidfuzz, diacritics-insensitive, ratio ≥ 85)
    nothing usable → 422 unreadable_link

search(name, city, neighborhood):
    Places Text Search(textQuery = f"{name} {neighborhood} {city}", languageCode = "ro", regionCode = "RO")
    up to 5 candidates; best = first result if its name matches

no_google_profile:
    place_id = null → chapter "profil" scores 0, single problem G01 "Creează-ți profilul Google"
```

### Step 2 — Canonical profile

**Place Details (New)** with a field mask:

| Purpose | Fields |
|---|---|
| Identity | `id`, `displayName`, `primaryType`, `primaryTypeDisplayName`, `types`, `businessStatus`, `googleMapsUri` |
| Contact | `formattedAddress`, `shortFormattedAddress`, `addressComponents`, `location`, `nationalPhoneNumber`, `internationalPhoneNumber`, `websiteUri` |
| Hours | `regularOpeningHours`, `currentOpeningHours` (special days) |
| Reputation | `rating`, `userRatingCount`, `reviews` (max 5, by relevance; fallback for R03) |
| Media & details | `photos` (max 10 returned), `editorialSummary`, `priceLevel`, `priceRange` |
| Attributes | `dineIn`, `takeout`, `delivery`, `outdoorSeating`, `servesCoffee`, `servesBreakfast`, `allowsDogs`, `goodForGroups`, `paymentOptions`, `accessibilityOptions` |

Normalize (§4), save as `canonical`, start the live test (3.8), then run the other collectors.

### Step 3 — Collectors

Each collector: `async collect(business) -> (list[SourceSnapshot], list[CheckResult])`.

| Collector | Timeout | Progress step |
|---|---|---|
| 3.1 Google profile | 15 s | `google` (with steps 1–2) |
| 3.2 Reviews | 30 s | `recenzii` |
| 3.3 Website | 45 s (PageSpeed inside: 40 s) | `website` |
| 3.4 Listings, 3.5 Mentions, 3.6 Social | 30 s each | `retele` (when all three finish) |
| 3.7 Probe, 3.8 Live test, 3.9 Competitors (top 3 details) | 30 s / 75 s / 15 s | `gemini` (when all three finish) |

A collector that times out or raises marks its checks `unknown`; the scan never fails because of one collector. Target total: under 90 s.

#### 3.1 Google profile → `profil`

Pure code on the canonical profile, one LLM call for the category, three self-reported answers.

```
G01 profile exists and businessStatus == OPERATIONAL   gate: no profile → chapter 0, only problem G01
G02 primary category fits the business                 L1 judge: business_type (+ website facts if ready) vs primaryType
G03 regular hours for all 7 days                       regularOpeningHours
G04 special/holiday hours set                          currentOpeningHours special days in the next 60 days
G05 at least 5 photos                                  len(photos): ≥5 pass, 3–4 partial, <3 fail (API caps at 10)
G06 website link set                                   websiteUri
G07 phone set                                          nationalPhoneNumber
G08 owner description present                          self_report.has_google_description (not in Places API)
G09 post in the last 30 days                           self_report.last_google_post
G10 key attributes filled for the type                 attribute fields relevant to business_type
G11 price level/range set                              priceLevel / priceRange
G12 profile claimed by the owner                       self_report.profile_claimed
```

Emit `google` done: „Am găsit Profilul tău Google”.

#### 3.2 Reviews → `recenzii`

```
google      = canonical.rating, canonical.review_count
recent      = SerpApi Google Maps Reviews (engine=google_maps_reviews, place_id, sort_by=newestFirst, hl=ro)
              first page, up to 20 reviews, each with date and owner response (if any)
              (if place_id isn't accepted, look up the data_id once with engine=google_maps)
median      = median(review_count of 3.9 nearby competitors)       # Nearby Search, not the live test

R01 review count vs competitor median     ≥ median full, ≥ 50% half, else fail
R02 rating                                ≥ 4.6 full, 4.3–4.5 partial, < 4.3 fail
R03 recency                               newest review ≤ 30 days full, ≤ 90 partial, else fail
                                          (SerpApi down → newest of Places' 5 reviews; still down → unknown)
R04 owner replies                         share of the recent reviews with an owner reply:
                                          ≥ 80 % full, ≥ 40 % partial, else fail
                                          title shows the count: "9 din ultimele 20 de recenzii fără răspuns"
R05 reviews on a second relevant platform platforms[] includes the one expected for the type
                                          (tripadvisor: cafenea/restaurant/bar · booking: hotel · booksy: salon)
                                          platforms = null → unknown
```

Emit `recenzii` done: „Am găsit {review_count} de recenzii”.

#### 3.3 Website → `continut` + `site`

```
if not has_website:
    continut and site → 0; top problem T09 offers the generated info page ("Fă-ți un site simplu")
    return

pages = [homepage] + up to 3 internal pages (sitemap.xml or nav links: menu, contact, about, services, FAQ)

for each page:
    raw = httpx GET, no JavaScript, 10 s                      # what non-Google AI crawlers see
    if looks_empty(raw):                                     # < 200 chars of visible text, OR business name/address
                                                             # from Google missing, OR an empty SPA shell
                                                             # (<div id="root"></div>, "enable JavaScript")
        rendered = Playwright render (lazy-launched, reused, 15 s)
    text = rendered or raw; store raw text, rendered text, and which was used

robots   = /robots.txt, parsed per user agent (urllib.robotparser)
sitemap  = /sitemap.xml (or the Sitemap: line in robots.txt)
jsonld   = <script type="application/ld+json"> blocks (selectolax + json)
links    = every <a href> on the pages → social links + JSON-LD sameAs (fed to 3.6)
speed    = PageSpeed Insights API, strategy=mobile, category=performance (runs in parallel, 40 s)
facts    = L2 extract(text of all pages) → WebsiteFacts:
           { name, what_it_is, address, neighborhood, phone, hours, menu_items_or_services,
             prices_present, menu_is_pdf_or_image, faq_items, language,
             page_with_basics: url | null }      # one page holding name + what + address + hours + phone
```

**Conținutul site-ului** (`continut`, on `facts` vs canonical):

```
C01 name + what the business is, visible on homepage (title / H1 / first text)
C02 address + neighborhood in page text
C03 hours in page text, matching Google
C04 phone in page text
C05 menu / products / prices as text (not only PDF or image)
C06 a page or section per main service/category
C07 answers to common questions (laptop, Wi-Fi, parking, pets, reservations)
C08 content in Romanian
```

**Site-ul, văzut de Gemini** (`site`, technical):

```
T01 site reachable, HTTPS, status 200
T02 robots.txt allows Googlebot and Google-Extended
T03 robots.txt allows OAI-SearchBot, GPTBot, PerplexityBot, ClaudeBot
T04 key content in raw HTML: name, address, hours from Google found without JavaScript
    (fails if they only appear after the Playwright render)
T05 sitemap.xml exists and lists the main pages
T06 LocalBusiness / CafeOrCoffeeShop JSON-LD present, matching NAP
T07 mobile speed: PageSpeed performance ≥ 90 full, 50–89 partial, < 50 fail
    (PageSpeed fails → time to first byte: < 0.8 s full, < 1.8 s partial, else fail)
T08 mobile viewport meta tag present
T09 one page with the basics (facts.page_with_basics) → fix: the generated info page

gate: T01 fails, or T02 blocks Googlebot, or T04 finds an empty shell
      → cap continut at 30 (Gemini can't read that content anyway)
```

Emit `website` done: „Am citit {domain}”.

#### 3.4 Listings → `info`

Only links the owner gave (onboarding social links and platform links found on the website); no searching for missing platforms.

```
expected = platforms expected for business_type
           (cafenea: Instagram, TripAdvisor, plus Glovo/Wolt/Bolt Food if canonical.delivery)
           (salon: Instagram, Booksy · hotel: Instagram, Booking)

for each known URL:
    fetch (raw first; Playwright if empty), L3 extract → { name, address, phone, hours }
    normalize (§4), compare field by field with canonical
    blocked / login wall → that source unknown, excluded from L02

L01 coverage: share of expected platforms the owner is on (onboarding links + platforms[])   (30)
L02 consistency: matched / compared fields across readable sources                         (70)
    each mismatch is its own problem, check_id "L02:<source>:<field>",
    e.g. "Telefonul de pe Glovo e diferit de cel de pe Google"
```

#### 3.5 Mentions → `mentiuni`

Titles and domains only; no page reading.

```
queries = [
  f'"{name}" {city}',
  f'"{name}" {neighborhood}',
  f'cele mai bune {type_plural} {neighborhood}',
  f'top {type_plural} {city}',
  f'"{name}" recenzie',
]
for each query: Gemini + Google Search grounding (live model, free tier: 500 Search-grounded requests/day) → groundingMetadata.groundingChunks
    chunk.web.title is the domain; chunk.web.uri is a vertexaisearch redirect
    → follow the redirect (GET, follow_redirects, read no body) to get the real URL for display

drop: own website, social profiles, listing platforms from 3.4, google.com
L4 classify each remaining (title, domain, cited answer segment)
   → { mentions_business: bool, type: news | blog | list | forum | other }

M01 distinct third-party domains mentioning the business   0 / 1–2 / 3–5 / 6+ → 0 / 15 / 30 / 45   (45)
M02 included in at least one best-of / top list                                              (25)
M03 a local news or press mention                                                            (15)
M05 a forum / community mention                                                              (15)
```

(M04 "mention in the last 12 months" is dropped in v1: it needs page dates.)

#### 3.6 Social → `social`

Instagram and TikTok only; Facebook is not part of the product.

```
links  = onboarding URLs ∪ links found on the website (3.3)
ig     = Instagram Graph API Business Discovery for the handle (GET https://graph.facebook.com/v27.0/...):
         GET /{META_IG_USER_ID}?fields=business_discovery.username({handle})
             {biography,website,followers_count,media_count,media.limit(10){timestamp}}
         works only for business/creator accounts; personal account or no token → ig = null

S02 Instagram profile exists                               ig != null, else HTTP status of the profile URL      (25)
S03 posted in the last 30 days                             newest ig media timestamp; ig null → self_report.last_social_post   (30)
S04 cross-links: website ↔ Instagram ↔ Google profile      website links to Instagram, ig.website points to the site,
                                                           canonical.website set                                 (20)
S05 Instagram bio says what + where (+ link or hours)      L1-style judge on ig.biography; ig null → unknown     (25)
```

(S01, the old Facebook check, is removed; the other IDs stay as they were.)

Emit `retele` done when 3.4, 3.5 and 3.6 finish: „Am verificat Instagram”.

#### 3.7 Training-data probe → `cunoaste`

```
Gemini API, NO tools, fast tier, each prompt run 3 times:
  P1: f"Ce știi despre {name} din {neighborhood}, {city}?"
  P2: f"Recomandă câteva {type_plural} din {neighborhood}."
L7 judge (one call) compares the six answers with canonical:

K01 knows the business exists (P1 in ≥ 2 of 3 runs, or named in any P2 run)   (50)
K02 knows the correct type and neighborhood                                   (30)
K03 states no wrong facts                                                     (20)

no direct fixes → chapter card shows "Crește pe măsură ce rezolvi restul"
```

#### 3.8 Live Gemini test → `gemini` block (+ Screen 5)

```
1. L5 generates 12 Romanian prompts from type, city, neighborhood and canonical attributes, 4 per group:
   general  : "cea mai bună cafenea din București", ...
   cartier  : "cafenea în Cotroceni", "cafenea lângă Palatul Cotroceni", ...
   situatii : "cafenea unde pot lucra cu laptopul", "cafenea unde pot veni cu câinele", ...

2. Run each prompt 3 times (36 calls, live model on the free tier: 500 Maps-grounded requests/day;
   keep concurrency under the free tier's rate limit):
   tools = [Google Maps grounding]   (gemini-2.5-flash-lite can't add Search grounding in the same call)
   toolConfig.retrievalConfig = { latLng: neighborhood/business location, languageCode: "ro-RO" }
   no system prompt, no business context: only the customer's question

3. Parse each answer:
   mentioned   = target place_id in groundingChunks[].maps.placeId
                 OR fuzzy name match in the text (diacritics-insensitive)
   position    = order of first appearance among businesses named (L6 as backup)
   others      = other place IDs / names in the answer
   facts_ok    = L6/L7: stated hours/address for the target vs canonical
   sources     = maps chunks (title + uri)

4. Aggregate:
   a prompt is "mentioned" if the target appears in ≥ 2 of 3 runs → "Apari în X din 12 răspunsuri"
   top 3 competitors = most frequently mentioned other businesses

score:
  mention rate     (70)   70 × X / 12
  average position (15)   1st = 15, 2nd–3rd = 8, later = 0; never mentioned = 0
  facts correct    (15)   never mentioned → unknown (score over 85)
```

#### 3.9 Competitors

```
nearby  = Places Nearby Search (New): includedTypes for business_type, circle(location, 1.5 km),
          rankPreference = POPULARITY, top 3 → feeds R01 right after step 2
rivals  = top 3 from the live test (3.8) → Place Details (same fields as step 2)
compare rows (me + rivals): review_count, rating, photo_count (capped at 10 → "10+"),
                            hours_complete (7 days + special days)
insights_ro / actions: code templates comparing me vs the rivals' median
```

### Step 4 — Normalize & cross-check

Rules from this table, implemented with `phonenumbers` (libphonenumber) and `rapidfuzz`:

| Field | Rules |
|---|---|
| Address | lowercase; strip diacritics and unify ș/ş, ț/ţ; expand abbreviations (Str. → strada, Bd./Bdul → bulevardul, Nr. → numărul, Sect. → sector, Calea, Șos. → șoseaua); compare street + number + sector, ignore formatting |
| Phone | `phonenumbers.parse(x, "RO")` → E.164; `07xx…`, `+407xx…`, `00407xx…` all become `+407xx…` |
| Hours | parse into `{day: [(open, close)]}`; accept "L–V", "Luni–Vineri", "Mon–Fri", "non-stop" |
| Name | strip legal suffixes (SRL, S.R.L.), quotes, diacritics; `rapidfuzz.fuzz.token_sort_ratio ≥ 85` |

Only flag **real** mismatches (different number, street, phone digits or hours). "Str." vs "Strada" is the same address after normalization and never becomes a problem card.

### Step 5 — Scoring

```
chapter_score = round(100 × Σ points_earned / Σ points_max)    # over checks that are not "unknown";
                                                               # claimed_fixed checks count as fully earned
                                                               # every check unknown → score null
apply gates/caps (T-gate on continut; no website → continut and site 0; no Google profile → profil 0)

overall_exact = Σ weight[ch] × chapter_score[ch] / Σ weight[ch]   # over the 8 chapters + gemini with a score
overall       = round(overall_exact)

weights:
  profil      Profilul Google                0.20
  recenzii    Recenzii                       0.15
  continut    Conținutul site-ului           0.15
  site        Site-ul, văzut de Gemini       0.10
  info        Aceleași informații peste tot  0.10
  mentiuni    Mențiuni pe alte site-uri      0.10
  social      Rețele sociale                 0.05
  cunoaste    Te cunoaște deja Gemini?       0.05
  gemini      Vizibilitate în Gemini         0.10   (not a chapter in the UI)
```

Check: the design's mock scores (65/50/35/50/35/25/55/20, Gemini 17) give `overall_exact` 42.2 → 42.

#### Check catalog (points per chapter = 100)

| Chapter | Check | Points | Data source | Fix type |
|---|---|---|---|---|
| profil | G02 category | 10 | Places + L1 | owner_action |
| | G03 regular hours | 15 | Places | owner_action |
| | G04 special hours | 10 | Places | owner_action |
| | G05 ≥ 5 photos | 10 | Places | owner_action |
| | G06 website link | 10 | Places | owner_action |
| | G07 phone | 10 | Places | owner_action |
| | G08 description | 10 | self-report | generate |
| | G09 recent post | 5 | self-report | generate (post idea) |
| | G10 attributes | 5 | Places | owner_action |
| | G11 price range | 5 | Places | owner_action |
| | G12 profile claimed | 10 | self-report | owner_action |
| recenzii | R01 count vs competitors | 30 | Places + Nearby Search | owner_action (review link/QR) |
| | R02 rating | 20 | Places | owner_action |
| | R03 recency | 25 | SerpApi (fallback Places) | owner_action |
| | R04 owner replies | 15 | SerpApi | generate (reply drafts) |
| | R05 second platform | 10 | onboarding platforms | owner_action |
| continut | C01 name + what | 15 | L2 | generate |
| | C02 address + area | 15 | L2 | generate |
| | C03 hours match | 15 | L2 | generate |
| | C04 phone | 10 | L2 | generate |
| | C05 menu as text | 15 | L2 | generate |
| | C06 page per service | 10 | L2 | dev_export |
| | C07 FAQ | 10 | L2 | generate |
| | C08 Romanian | 10 | L2 | generate |
| site | T01 reachable/HTTPS | 15 | HTTP | dev_export |
| | T02 Google crawlers allowed | 20 | robots.txt | dev_export |
| | T03 other AI crawlers allowed | 10 | robots.txt | dev_export |
| | T04 content in raw HTML | 20 | raw HTML (+ Playwright) | dev_export |
| | T05 sitemap | 5 | HTTP | dev_export |
| | T06 LocalBusiness JSON-LD | 10 | HTML parse | dev_export (filled snippet) |
| | T07 mobile speed | 5 | PageSpeed (fallback TTFB) | dev_export |
| | T08 mobile viewport | 5 | HTML parse | dev_export |
| | T09 page with the basics | 10 | L2 | generate (info page) |
| info | L01 coverage | 30 | onboarding + website links | owner_action |
| | L02 consistency | 70 | fetch + L3 + §4 | owner_action |
| mentiuni | M01 domains count | 45 | Search grounding + L4 | owner_action |
| | M02 best-of list | 25 | Search grounding + L4 | owner_action (outreach message) |
| | M03 local press | 15 | Search grounding + L4 | generate (pitch email) |
| | M05 forum mention | 15 | Search grounding + L4 | — |
| social | S02 Instagram | 25 | Instagram Business Discovery | owner_action |
| | S03 recent post | 30 | Instagram (fallback self-report) | generate (post ideas) |
| | S04 cross-links | 20 | website links + Instagram + Places | owner_action |
| | S05 Instagram bio | 25 | Instagram + judge | generate (Instagram bio) |
| cunoaste | K01–K03 | 50/30/20 | Gemini, no tools + L7 | — |
| gemini | mention rate / position / facts | 70/15/15 | Gemini + Maps & Search grounding | — |

### Step 6 — Problems & fixes

```
for each check with status in (fail, partial) and not claimed_fixed:
    problem.points = chapter-score gain if fixed
                   = round(100 × (points_max − points_earned) / Σ points_max of known checks)
    problem.impact = problem.points × weight[chapter]            # overall points, used for sorting
    problem.title_ro, why_ro, steps_ro = Romanian template per check_id (problems.py),
                                         filled with evidence ("Doar 2 fotografii, recomandat minim 5")
    problem.fix.panel:
        S05, G08, C0x, G09, R04, M03, S03 → generate_text   (texts written on demand by Dev A's generator)
        T09                               → info_page
        dev_export checks                 → dev_export
        everything else                   → steps

passed checks → SolvedItem with a "solved" template ("Numărul de telefon e afișat")
sort problems inside a chapter by points; next_steps = top 3 open problems by impact overall
```

Copy for titles and reasons comes from the design artboards wherever a check appears there (`design/Capitol.dc.html`, `Rezolva.dc.html`, `FisaInfo.dc.html`, `Panou.dc.html`); write new templates in the same plain, jargon-free Romanian for the rest.

**Developer export** (Dev A, `GET /dev-export`): one Markdown document; for each `dev_export` problem: what's wrong (one line), evidence (URL, what we found), exact fix (robots.txt lines, a JSON-LD snippet filled with the café's data, "serve the menu as HTML text, not a PDF"), how to verify (`curl -A 'GPTBot' https://…`).

### Step 7 — Report, re-test

```
report = Report (contract.md), saved as JSON on the scan row

"Am rezolvat" / assistant confirm:
    claimed_fixed = true on the check, recompute scores and problems, save, return ScoreUpdate
    (verified on the next scan; Google changes can take days to show up)

"Testează din nou": rerun 3.8 only, recompute gemini + overall, update last_checked
"Analizează din nou": new scan with the same inputs
```

---

## 4. LLM calls

All structured JSON output except L8. Tiers: `fast` (`gemini-3.5-flash-lite`) for extraction and judging; `smart` (`gemini-3.8-flash`) for texts and chat; all on the free-tier `GEMINI_API_KEY`. Grounded calls (live test, mentions) use the `live` model (`gemini-2.5-flash-lite`), the newest model with grounding on the free tier (500 Maps-grounded and 500 Search-grounded requests a day).

| ID | Purpose | Tier | Output |
|---|---|---|---|
| L1 | Category judge (G02), Instagram bio judge (S05) | fast | `{fits: bool, reason}` |
| L2 | Website fact extraction | fast | `WebsiteFacts` |
| L3 | Listing extraction | fast | `{name, address, phone, hours}` |
| L4 | Mention classification | fast | `{mentions_business, type}` |
| L5 | Live-test prompt generation | fast | 12 prompts in 3 groups |
| L6 | Answer parsing (backup to grounding) | fast | `{businesses_in_order[], stated_facts}` |
| L7 | Training-data judge | fast | `{knows, correct_type_area, wrong_facts[]}` |
| L8 | Fix texts, info page, dev instructions (Dev A) | smart | text |
| L9 | Assistant chat with function calling (Dev A) | smart | reply + function calls |

---

## 5. Orchestration skeleton

```python
async def run_pipeline(scan_id: str) -> None:
    business = Business.from_inputs(load_inputs(scan_id))

    emit("google", "running")
    business.place_id = business.inputs.place_id or await resolve_place(business.inputs)   # Step 1
    business.canonical = await build_canonical(business.place_id)                         # Step 2

    live = asyncio.create_task(with_timeout(live_test(business), 75))                     # 3.8, slowest
    nearby = await with_timeout(nearby_competitors(business), 15)                         # 3.9a, feeds R01

    google = await with_timeout(google_profile(business), 15)                             # 3.1
    emit("google", "done", "Am găsit Profilul tău Google")

    results = await asyncio.gather(
        step("recenzii", reviews(business, nearby), 30),                                  # 3.2
        step("website", website(business), 45),                                           # 3.3
        step("retele", gather3(listings(business), mentions(business), social(business)), 30),  # 3.4–3.6
        step("gemini", gather3(training_probe(business), live, rivals(business, live)), 75),   # 3.7–3.9b
    )                                                                                      # failures → unknown

    business.sources, business.checks = merge(google, *results)
    cross_check(business)                                                                  # Step 4
    scores = score(business.checks, WEIGHTS, GATES)                                        # Step 5
    problems = build_problems(business, scores)                                            # Step 6
    save_report(scan_id, assemble_report(business, scores, problems))                      # Step 7
    emit_complete(scan_id)
```

---

## 6. Error handling

| Situation | Behavior |
|---|---|
| Maps link can't be resolved | `422 unreadable_link` → `Eroare` state: retry, „Caută-mă pe Google”, or skip |
| No Google profile | `profil` = 0, top problem G01 „Creează-ți profilul Google”; live test still runs |
| Website down / blocked | T01 fails, content checks `unknown`, dev export explains |
| Platform page blocks fetch | that source `unknown`, excluded from the L02 denominator |
| Collector timeout or exception | its checks `unknown`, chapter shows „Nu am putut verifica” |
| SerpApi down / quota | R03 falls back to Places reviews; R04 `unknown` |
| PageSpeed timeout | T07 falls back to time to first byte |
| No Meta token / personal Instagram account | S02 from HTTP status, S03 from self-report, S05 `unknown` |
| Gemini error / rate limit | retry with exponential backoff (3 tries); still failing → `gemini.status = "unknown"`, overall renormalized without it |

---

## 7. Cost and latency (rough, per scan)

| Step | Calls |
|---|---|
| Places (Details + Nearby + 3 competitor Details; search/resolve during onboarding) | ~5–8 |
| SerpApi | 1–2 (free plan: 250 searches/month; cache during development) |
| PageSpeed | 1 |
| Meta Business Discovery | 1 |
| Website fetches | ~4 raw; rendered only for empty pages |
| Listing fetches + mention redirects | ~10–20 |
| LLM extraction/classification | ~20–30 |
| Live test | 36 grounded Gemini calls |
| Training probe | 6 + 1 judge |

---

## 8. Where each piece of data comes from

| Chapter | Data | Source |
|---|---|---|
| Onboarding | Business identity (`place_id`) | Places API (New): Text Search; Maps link resolved by redirect + Text Search |
| profil | Category, hours (incl. special days), website, phone, photos, attributes, status, price | Places API (New): Place Details |
| profil | Owner description, recent posts, claimed status | Onboarding self-report |
| recenzii | Rating and review count | Place Details |
| recenzii | Review dates and owner replies | SerpApi Google Maps Reviews, sorted by newest |
| recenzii | Competitor review counts | Places Nearby Search + Place Details |
| recenzii | Second review platform | Onboarding platform chips |
| continut | Page text | `httpx` raw HTML; Playwright only for empty pages |
| continut | Services, hours, prices, FAQ, NAP, language | Gemini (fast tier) with a JSON schema |
| site | robots.txt, raw HTML, HTTPS, sitemap | `httpx` |
| site | Crawler rules per AI bot | `urllib.robotparser` |
| site | JavaScript-only content | raw vs Playwright-rendered text |
| site | Schema markup | JSON-LD script-tag parse (`selectolax`) |
| site | Mobile speed | PageSpeed Insights API (fallback: time to first byte) |
| info | Name, address, phone, hours per source | Data already collected + fetched owner-provided listing pages |
| info | Matching | `phonenumbers` + `rapidfuzz` with the §4 rules |
| mentiuni | Third-party pages mentioning the business | Gemini + Google Search grounding; domains from chunk titles, URLs by following the redirect |
| social | Instagram / TikTok links | Onboarding + website links and JSON-LD `sameAs` |
| social | Instagram bio, website, posts, last post date | Instagram Graph API: Business Discovery |
| cunoaste | Gemini's answer without search | Gemini API, no tools, 2 prompts × 3 runs |
| cunoaste | Correct / unknown / wrong verdict | Gemini as judge, compared with Places data |
| gemini | 12 Romanian prompts | Gemini, generated from Places data |
| gemini | Answers and sources | Gemini with Google Maps + Google Search grounding, business coordinates in the retrieval config |
| gemini | Mentioned, position, facts correct | `placeId` match in Maps grounding chunks + Gemini extraction |

---

## 9. Known limitations

- **Places API limits:** at most 5 reviews (by relevance) and 10 photos. SerpApi covers review dates and replies; photo counts above 10 show as "10+".
- **Owner description and posts aren't in any public API.** The Business Profile API needs access approval (~14 days) and the owner's OAuth consent; v1 uses self-report. Later: „Conectează profilul Google”.
- **Instagram Business Discovery** only works for business and creator accounts. It needs a Meta app with Facebook Login and a Facebook Page linked to our own Instagram professional account; that Page is setup only, the product never checks Facebook. Meta's Instagram Login setup (no Page) can't read other accounts. Personal accounts fall back to self-report and `unknown`.
- **Gemini API ≠ the consumer Gemini app.** Grounded API answers are a close proxy. Say „testat cu Gemini”.
- **Search grounding links are redirects;** following them costs one request each.
- **Maps grounding language and API:** Google's Maps grounding page (14 November 2026) says it "currently only supports English language prompts and responses", and its examples use the Interactions API (`client.interactions.create`, tool `{"type": "google_maps", "latitude", "longitude"}`) rather than `generateContent` with `toolConfig.retrievalConfig`. Verify both with a real call before building the live test; if Romanian prompts don't return Maps chunks, report it before changing the design.
- **To verify:** whether `currentOpeningHours` reliably exposes holiday hours; whether SerpApi accepts `place_id` directly for reviews; how `Google-Extended` affects Gemini grounding.
- **Not in v1:** Facebook (dropped from the product), Tripadvisor data, Bing Places, Apple Maps, Romanian directories, ChatGPT as a second engine, mention dates (M04).

---

## Sources

- Places API (New) — Place resource: https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places
- Places API (New) — Place Details: https://developers.google.com/maps/documentation/places/web-service/place-details
- Gemini API — Grounding with Google Maps: https://ai.google.dev/gemini-api/docs/maps-grounding
- SerpApi — Google Maps Reviews API: https://serpapi.com/google-maps-reviews-api
- Instagram Platform — Business Discovery: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery
- PageSpeed Insights API: https://developers.google.com/speed/docs/insights/v5/get-started
- Google Business Profile APIs — FAQ: https://developers.google.com/my-business/content/faq
- Vercel — The rise of the AI crawler: https://examples.vercel.com/blog/the-rise-of-the-ai-crawler
