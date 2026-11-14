# LLM Visibility — Data Retrieval Resources

| Category | Resource needed | How to get it |
|---|---|---|
| Onboarding | Business identity (`place_id`) | Google Places API (New): Autocomplete / Text Search |
| 1. Google Maps profile | Category, hours (incl. holidays), website, photos, attributes, status | Google Places API (New): Place Details |
| 1. Google Maps profile | Owner description | Web scraping of the public Google Maps listing |
| 1. Google Maps profile | Claimed status | Onboarding question (Da / Nu / Nu știu) |
| 2. Reviews | Google rating and review count | Google Places API (New): Place Details |
| 2. Reviews | Google review dates and owner replies | SerpApi: Google Maps Reviews endpoint, sorted by newest |
| 2. Reviews | Tripadvisor rating, count, ranking | Tripadvisor Content API: Location Search + Location Details |
| 2. Reviews | Full Tripadvisor review list (dates, owner replies) | Scraping service (e.g. Apify Tripadvisor reviews actor), only for restaurants, cafés, hotels |
| 3. Website content *(to be completed later)* | Page text from the site | Firecrawl (or `fetch` + cheerio/BeautifulSoup) |
| 3. Website content *(to be completed later)* | Services, hours, prices, FAQs, name/address/phone, language | LLM API (Gemini or Claude) with a JSON rubric |
| 4. AI-readable website | robots.txt, raw HTML, HTTPS, sitemap | HTTP `fetch` |
| 4. AI-readable website | Crawler rules per AI bot | `urllib.robotparser` (Python) or `robots-parser` (npm) |
| 4. AI-readable website | JavaScript-only content check | Playwright (rendered vs raw HTML) |
| 4. AI-readable website | Schema markup | `extruct` (Python) or JSON-LD script-tag parse |
| 4. AI-readable website | Speed and mobile score | Google PageSpeed Insights API |
| 5. Same info everywhere | Name, address, phone, hours from each source | Data already collected (Places, website, Tripadvisor, Instagram) |
| 5. Same info everywhere | Phone and name/address matching | `libphonenumber` + `rapidfuzz` |
| 6. Mentions on other sites | Third-party pages mentioning the business, with links | Gemini API with Google Search grounding (one request); links from `groundingMetadata.groundingChunks`, resolved with a HEAD request |
| 7. Social media | Instagram / TikTok links | Website crawl (page links and JSON-LD `sameAs`) |
| 7. Social media | Instagram followers, posts, bio, website, last post date | Instagram Graph API: Business Discovery |
| 8. Does AI know you? | Gemini's answer without search | Gemini API, no tools, run 3 times |
| 8. Does AI know you? | Correct / unknown / wrong verdict | LLM API as judge, compared with Places data |
| 9. Live AI test | 10–20 Romanian prompts | LLM API, generated from Places data |
| 9. Live AI test | Gemini answers and sources | Gemini API with Google Search + Google Maps grounding, business coordinates in retrieval config |
| 9. Live AI test | Mentioned, position, facts correct | LLM API extraction + `place_id` match from Maps grounding chunks |
