"""3.3 Website → `continut` + `site`: what the site says (C01–C08) and whether Gemini can read it (T01–T09)."""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import phonenumbers
from pydantic import BaseModel
from selectolax.lexbor import LexborHTMLParser

from app import cache
from app.config import get_settings
from app.llm.client import json_call
from app.models import FaqItem, ScanInputs, WebsiteFacts
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.fetch import FetchedPage, fetch_page, fetch_raw, get_today, is_empty_shell
from app.pipeline.normalize import (
    get_address_parts,
    get_hours_mismatch_days,
    get_name_key,
    normalize_address,
    normalize_phone,
    parse_hours,
    strip_diacritics,
)
from app.pipeline.scoring import get_check_result, get_unknown_results
from app.pipeline.types import CheckResult, Evidence

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "llm" / "prompts"
"""The directory holding the LLM prompt templates."""

CONTENT_CHECK_IDS = [f"C0{number}" for number in range(1, 9)]
"""The content checks (`continut`)."""

TECH_CHECK_IDS = [f"T0{number}" for number in range(1, 10)]
"""The technical checks (`site`)."""

MAX_EXTRA_PAGES = 3
"""How many internal pages are read besides the homepage."""

PAGE_KINDS = {
    "contact": "contact",
    "meniu": "menu",
    "menu": "menu",
    "preturi": "menu",
    "oferta": "menu",
    "despre": "about",
    "about": "about",
    "servicii": "services",
    "services": "services",
    "faq": "faq",
    "intrebari": "faq",
}
"""Words in a link or path that mark a page worth reading, and the kind of page each means."""

PAGE_KIND_PRIORITY = ("contact", "menu", "about", "services", "faq")
"""The order in which page kinds are picked when there are more than three."""

SKIPPED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".zip", ".xml")
"""Links to files rather than pages."""

PAGE_TEXT_LIMIT = 6000
"""How much of each page's text the extraction reads."""

EXTRACTION_TIMEOUT_SECONDS = 25
"""The time limit of the website extraction call."""

GOOGLE_BOTS = ("Googlebot", "Google-Extended")
"""Google's crawlers, checked by T02."""

OTHER_AI_BOTS = ("OAI-SearchBot", "GPTBot", "PerplexityBot", "ClaudeBot")
"""The other AI crawlers, checked by T03."""

LOCAL_BUSINESS_TYPES = {
    "LocalBusiness",
    "CafeOrCoffeeShop",
    "Restaurant",
    "FoodEstablishment",
    "BarOrPub",
    "Bakery",
    "IceCreamShop",
    "HairSalon",
    "BeautySalon",
    "NailSalon",
    "DaySpa",
    "HealthAndBeautyBusiness",
    "Hotel",
    "LodgingBusiness",
    "Store",
}
"""Schema.org types that count as LocalBusiness structured data for T06."""

CommonQuestion = Literal["laptop", "wifi", "parcare", "animale", "rezervari"]
"""The common customer questions C07 looks for answers to."""

COMMON_QUESTION_COUNT = 5
"""How many common questions C07 asks about."""

PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
"""The PageSpeed Insights API endpoint."""

PAGESPEED_TIMEOUT_SECONDS = 40
"""How long the PageSpeed run may take."""

TIME_RANGE_PATTERN = re.compile(r"\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2}")
"""Opening hours written as a time range, e.g. „8:00–20:00”."""

UNREACHABLE_RO = "Site-ul nu s-a deschis când l-am verificat."
"""Why the site checks couldn't run when the homepage didn't open."""

UNREADABLE_RO = "Nu am putut citi acum textul site-ului."
"""Why the content checks couldn't run when the extraction failed."""


class SiteExtraction(BaseModel):
    """What the L2 extraction reads from the website's text."""

    name: str | None
    what_it_is: str | None
    address: str | None
    neighborhood: str | None
    phone: str | None
    hours: str | None
    menu_items_or_services: list[str]
    prices_present: bool
    menu_is_pdf_or_image: bool
    faq_items: list[FaqItem]
    common_questions_answered: list[CommonQuestion]
    has_category_pages: bool
    language: str | None
    page_with_basics: str | None


class WebsiteScan(BaseModel):
    """The website collector's result: its checks, the facts read from the site and every link found on it."""

    checks: list[CheckResult]
    facts: WebsiteFacts | None
    links: list[str]


class SiteFiles(BaseModel):
    """What the site tells crawlers: robots.txt rules and the pages its sitemap lists."""

    robots_lines: list[str]
    sitemap_urls: list[str]

    def get_robots(self) -> RobotFileParser:
        """Returns a parser of the robots.txt rules (none means everything is allowed)."""
        parser = RobotFileParser()
        parser.parse(self.robots_lines)
        return parser


def get_website_url(inputs: ScanInputs, canonical: CanonicalProfile | None) -> str | None:
    """Returns the site's address with a scheme, from Google or the owner's answer."""
    website = (canonical.website if canonical else None) or (inputs.website_url if inputs.has_website else None)
    if not website:
        return None
    return website if website.startswith(("http://", "https://")) else f"https://{website}"


async def collect_website(inputs: ScanInputs, canonical: CanonicalProfile | None) -> WebsiteScan:
    """Returns the website checks; no site makes both chapters 0, an unreachable one fails T01 and leaves the rest unknown."""
    url = get_website_url(inputs, canonical)
    if url is None:
        return get_no_website_scan()
    name = canonical.name if canonical else inputs.business_name
    speed_task = asyncio.create_task(get_mobile_speed(url))
    try:
        homepage = await fetch_page(url, get_expected_terms(name, canonical))
        if homepage is None or homepage.raw.status >= 400:
            return get_unreachable_scan(url, homepage)
        origin = get_origin(homepage.raw.final_url)
        files = await get_site_files(origin)
        extra_urls = pick_extra_pages(homepage, files.sitemap_urls, origin)
        extra_pages = await asyncio.gather(*(fetch_page(extra_url, []) for extra_url in extra_urls))
        pages = [homepage, *[page for page in extra_pages if page is not None and page.raw.status < 400]]
        extraction = await get_extraction(inputs, name, pages)
        speed = await speed_task
    finally:
        speed_task.cancel()
    jsonld = get_jsonld(pages)
    checks = get_content_checks(inputs, name, canonical, homepage, pages, extraction) + get_tech_checks(
        name, canonical, homepage, pages, files, jsonld, extraction, speed
    )
    return WebsiteScan(checks=checks, facts=get_website_facts(extraction), links=get_links(pages, jsonld))


def get_no_website_scan() -> WebsiteScan:
    """Returns the scan of a business without a site: both chapters fail, and the info page (T09) is the way in."""
    evidence = Evidence(found="Nu ai încă un site.")
    checks = [get_check_result("T09", "fail", evidence)] + [
        get_check_result(check_id, "fail", evidence) for check_id in CONTENT_CHECK_IDS
    ]
    return WebsiteScan(checks=checks, facts=None, links=[])


def get_unreachable_scan(url: str, homepage: FetchedPage | None) -> WebsiteScan:
    """Returns the scan of a site that didn't open: T01 fails and caps the content, everything else is unknown."""
    found = f"Site-ul a răspuns cu eroarea {homepage.raw.status}." if homepage else "Site-ul nu a răspuns."
    t01 = get_check_result("T01", "fail", Evidence(found=found, url=url), gate=True)
    unknown = get_unknown_results(CONTENT_CHECK_IDS + TECH_CHECK_IDS[1:], UNREACHABLE_RO)
    return WebsiteScan(checks=[t01, *unknown], facts=None, links=[])


def get_expected_terms(name: str, canonical: CanonicalProfile | None) -> list[str]:
    """Returns words a real page about the business would contain: the longer words of its name and street."""
    street = get_address_parts(canonical.formatted_address).street if canonical and canonical.formatted_address else None
    words = get_name_key(name).split() + (street.split() if street else [])
    return [word for word in words if len(word) > 3 and word not in ("strada", "bulevardul", "doctor")]


def get_origin(url: str) -> str:
    """Returns a URL's scheme and host, e.g. `https://example.ro`."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


async def get_site_files(origin: str) -> SiteFiles:
    """Returns the site's robots.txt rules and the page URLs its sitemap lists (following one sitemap index level).

    robots.txt and the default sitemap.xml are fetched together; a robots.txt that redirects elsewhere isn't read as rules.
    """
    robots, default_locations = await asyncio.gather(
        fetch_raw(f"{origin}/robots.txt"), get_sitemap_locations(f"{origin}/sitemap.xml")
    )
    is_robots = robots is not None and robots.status < 400 and urlparse(robots.final_url).path == "/robots.txt"
    robots_lines = robots.html.splitlines() if robots is not None and is_robots else []
    sitemap_locations = [line.split(":", 1)[1].strip() for line in robots_lines if line.lower().startswith("sitemap:")]
    sitemap_urls: list[str] = []
    for sitemap_url in sitemap_locations or [f"{origin}/sitemap.xml"]:
        is_default = sitemap_url == f"{origin}/sitemap.xml"
        locations = default_locations if is_default else await get_sitemap_locations(sitemap_url)
        child_sitemaps = [location for location in locations if location.endswith(".xml")]
        sitemap_urls += [location for location in locations if not location.endswith(".xml")]
        for child in child_sitemaps[:2]:
            sitemap_urls += [location for location in await get_sitemap_locations(child) if not location.endswith(".xml")]
        if sitemap_urls:
            break
    return SiteFiles(robots_lines=robots_lines, sitemap_urls=sitemap_urls)


async def get_sitemap_locations(url: str) -> list[str]:
    """Returns the `<loc>` URLs of one sitemap file, or none when it doesn't exist."""
    sitemap = await fetch_raw(url)
    if sitemap is None or sitemap.status >= 400:
        return []
    return [location.strip() for location in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", sitemap.html)]


def pick_extra_pages(homepage: FetchedPage, sitemap_urls: list[str], origin: str) -> list[str]:
    """Returns up to three internal pages worth reading, one per kind, contact first (it usually holds address, hours, phone)."""
    tree = LexborHTMLParser(homepage.raw.html)
    candidates = [
        (urljoin(homepage.raw.final_url, node.attributes.get("href") or ""), node.text(strip=True))
        for node in tree.css("a[href]")
    ]
    candidates += [(url, "") for url in sitemap_urls]
    first_by_kind: dict[str, str] = {}
    for url, label in candidates:
        clean = url.split("#")[0].rstrip("/")
        if not clean.startswith(origin) or clean == origin or clean.lower().endswith(SKIPPED_EXTENSIONS):
            continue
        haystack = strip_diacritics(f"{urlparse(clean).path} {label}")
        kind = next((kind for word, kind in PAGE_KINDS.items() if word in haystack), None)
        if kind and kind not in first_by_kind:
            first_by_kind[kind] = clean
    return [first_by_kind[kind] for kind in PAGE_KIND_PRIORITY if kind in first_by_kind][:MAX_EXTRA_PAGES]


async def get_extraction(inputs: ScanInputs, name: str, pages: list[FetchedPage]) -> SiteExtraction | None:
    """Returns the facts the L2 extraction reads from the pages, or `None` when it fails or takes too long."""
    pages_text = "\n\n".join(f"## {page.raw.final_url}\n{page.text[:PAGE_TEXT_LIMIT]}" for page in pages)
    prompt = (
        (PROMPTS_DIR / "website_extract.md")
        .read_text(encoding="utf-8")
        .format(
            name=name,
            type_label=inputs.business_type_label_ro.lower(),
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            pages=pages_text,
        )
    )
    try:
        return await asyncio.wait_for(json_call(prompt, SiteExtraction), EXTRACTION_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Website extraction failed")
        return None


async def get_mobile_speed(url: str) -> int | None:
    """Returns the PageSpeed mobile performance score (0–100), or `None` when the run fails; cached per day."""
    key = ["pagespeed", get_today(), url]
    cached = cache.get(key)
    if cached is not None:
        return cached
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if get_settings().pagespeed_api_key:
        params["key"] = get_settings().pagespeed_api_key
    try:
        async with httpx.AsyncClient(timeout=PAGESPEED_TIMEOUT_SECONDS) as client:
            response = await client.get(PAGESPEED_URL, params=params)
        response.raise_for_status()
        score = response.json()["lighthouseResult"]["categories"]["performance"]["score"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        logger.info("PageSpeed failed for %s", url, exc_info=True)
        return None
    if score is None:
        return None
    result = round(score * 100)
    cache.set(key, result)
    return result


def get_jsonld(pages: list[FetchedPage]) -> list[dict[str, Any]]:
    """Returns every JSON-LD object on the pages, `@graph` lists flattened."""
    objects: list[dict[str, Any]] = []
    for page in pages:
        for node in LexborHTMLParser(page.raw.html).css('script[type="application/ld+json"]'):
            try:
                data = json.loads(node.text())
            except ValueError:
                continue
            for item in data if isinstance(data, list) else [data]:
                if isinstance(item, dict):
                    objects += [entry for entry in item.get("@graph", [item]) if isinstance(entry, dict)]
    return objects


def get_links(pages: list[FetchedPage], jsonld: list[dict[str, Any]]) -> list[str]:
    """Returns every link on the pages plus the JSON-LD `sameAs` links, absolute and without duplicates."""
    links = [
        urljoin(page.raw.final_url, node.attributes.get("href") or "")
        for page in pages
        for node in LexborHTMLParser(page.raw.html).css("a[href]")
    ]
    for item in jsonld:
        same_as = item.get("sameAs", [])
        links += [same_as] if isinstance(same_as, str) else [link for link in same_as if isinstance(link, str)]
    return list(dict.fromkeys(link for link in links if link.startswith("http")))


def get_website_facts(extraction: SiteExtraction | None) -> WebsiteFacts | None:
    """Returns the website facts fix texts and the info page are written from."""
    if extraction is None:
        return None
    return WebsiteFacts(
        what_it_is=extraction.what_it_is,
        menu_items_or_services=extraction.menu_items_or_services,
        prices_present=extraction.prices_present,
        faq_items=extraction.faq_items,
        language=extraction.language,
    )


def get_content_checks(
    inputs: ScanInputs,
    name: str,
    canonical: CanonicalProfile | None,
    homepage: FetchedPage,
    pages: list[FetchedPage],
    extraction: SiteExtraction | None,
) -> list[CheckResult]:
    """Returns C01–C08: whether the site says who, what, where, when and what it costs, in Romanian."""
    if extraction is None:
        return get_unknown_results(CONTENT_CHECK_IDS, UNREADABLE_RO)
    url = homepage.raw.final_url
    text = " ".join(page.text for page in pages)
    normalized_text = normalize_address(text)
    name_found = get_name_key(name) in get_name_key(f"{get_title(homepage.raw.html)} {homepage.text[:500]}")
    street = get_address_parts(canonical.formatted_address).street if canonical and canonical.formatted_address else None
    street_found = bool(street) and street in normalized_text
    neighborhood_found = strip_diacritics(inputs.neighborhood) in strip_diacritics(text)
    return [
        get_check_result(
            "C01", get_both_status(name_found, extraction.what_it_is is not None), Evidence(found=extraction.what_it_is, url=url)
        ),
        get_check_result(
            "C02",
            get_both_status(street_found, neighborhood_found),
            Evidence(found=extraction.address, expected=canonical.formatted_address if canonical else None, url=url),
        ),
        get_hours_check(canonical, extraction, url),
        get_phone_check(canonical, text, extraction, url),
        get_menu_check(extraction, url),
        get_check_result("C06", "pass" if extraction.has_category_pages else "fail", Evidence(url=url)),
        get_questions_check(extraction, url),
        get_check_result(
            "C08", "pass" if extraction.language == "ro" else "fail", Evidence(found=extraction.language, expected="ro", url=url)
        ),
    ]


def get_title(html: str) -> str:
    """Returns the text of a page's `<title>`."""
    title = LexborHTMLParser(html).css_first("title")
    return title.text(strip=True) if title else ""


def get_both_status(first: bool, second: bool) -> Literal["pass", "partial", "fail"]:
    """Returns pass when both parts are there, partial for one, fail for none."""
    return "pass" if first and second else "partial" if first or second else "fail"


def get_hours_check(canonical: CanonicalProfile | None, extraction: SiteExtraction, url: str) -> CheckResult:
    """Returns C03: hours on the site, matching Google's."""
    expected = "; ".join(canonical.hours_ro) if canonical and canonical.hours_ro else None
    if not extraction.hours or not parse_hours(extraction.hours):
        return get_check_result("C03", "fail", Evidence(found="lipsește", expected=expected, url=url))
    mismatch = get_hours_mismatch_days(parse_hours(extraction.hours), canonical.weekly_hours) if canonical else []
    return get_check_result(
        "C03", "partial" if mismatch else "pass", Evidence(found=extraction.hours, expected=expected, url=url)
    )


def get_phone_check(canonical: CanonicalProfile | None, text: str, extraction: SiteExtraction, url: str) -> CheckResult:
    """Returns C04: a phone number on the site, the same as Google's."""
    phones = {
        phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
        for match in phonenumbers.PhoneNumberMatcher(text, "RO")
    }
    if extraction.phone and normalize_phone(extraction.phone):
        phones.add(normalize_phone(extraction.phone) or "")
    expected = canonical.phone_e164 if canonical else None
    status = "fail" if not phones else "pass" if expected is None or expected in phones else "partial"
    return get_check_result("C04", status, Evidence(found=", ".join(sorted(phones)) or None, expected=expected, url=url))


def get_menu_check(extraction: SiteExtraction, url: str) -> CheckResult:
    """Returns C05: the menu, products or services written as text, with prices."""
    if not extraction.menu_items_or_services:
        found = (
            "Meniul e doar o imagine sau un PDF."
            if extraction.menu_is_pdf_or_image
            else "Nu am găsit produsele sau serviciile pe site."
        )
        return get_check_result("C05", "fail", Evidence(found=found, url=url))
    if extraction.menu_is_pdf_or_image or not extraction.prices_present:
        found = "Meniul e doar o imagine sau un PDF." if extraction.menu_is_pdf_or_image else "Nu am găsit prețuri lângă produse."
        return get_check_result("C05", "partial", Evidence(found=found, url=url))
    return get_check_result("C05", "pass", Evidence(found=", ".join(extraction.menu_items_or_services[:5]), url=url))


def get_questions_check(extraction: SiteExtraction, url: str) -> CheckResult:
    """Returns C07: how many of the five common customer questions the site answers."""
    answered = len(set(extraction.common_questions_answered))
    status = "pass" if answered >= 3 else "partial" if answered >= 1 else "fail"
    found = f"Am găsit răspuns la {answered} din {COMMON_QUESTION_COUNT} întrebări obișnuite."
    return get_check_result("C07", status, Evidence(found=found, url=url))


def get_tech_checks(
    name: str,
    canonical: CanonicalProfile | None,
    homepage: FetchedPage,
    pages: list[FetchedPage],
    files: SiteFiles,
    jsonld: list[dict[str, Any]],
    extraction: SiteExtraction | None,
    speed: int | None,
) -> list[CheckResult]:
    """Returns T01–T09: whether Gemini and other AI crawlers can reach and read the site."""
    url = homepage.raw.final_url
    robots = files.get_robots()
    https = url.startswith("https://")
    t01 = get_check_result(
        "T01", "pass" if https else "partial", Evidence(found=None if https else "Site-ul se deschide fără HTTPS.", url=url)
    )
    sitemap_evidence = Evidence(
        found=f"{len(files.sitemap_urls)} pagini" if files.sitemap_urls else None, url=f"{get_origin(url)}/sitemap.xml"
    )
    has_viewport = LexborHTMLParser(homepage.raw.html).css_first('meta[name="viewport"]') is not None
    if extraction is None:
        t09 = get_check_result("T09", "unknown", reason_ro=UNREADABLE_RO)
    else:
        t09 = get_check_result(
            "T09", "pass" if extraction.page_with_basics else "fail", Evidence(found=extraction.page_with_basics, url=url)
        )
    return [
        t01,
        get_google_crawlers_check(robots, pages, url),
        get_other_crawlers_check(robots, url),
        get_raw_content_check(name, canonical, homepage),
        get_check_result("T05", "pass" if files.sitemap_urls else "fail", sitemap_evidence),
        get_structured_data_check(name, canonical, jsonld, url),
        get_speed_check(speed, homepage),
        get_check_result("T08", "pass" if has_viewport else "fail", Evidence(url=url)),
        t09,
    ]


def get_google_crawlers_check(robots: RobotFileParser, pages: list[FetchedPage], url: str) -> CheckResult:
    """Returns T02: whether robots.txt lets Googlebot and Google-Extended read the pages; blocking Googlebot caps the content."""
    blocked = {
        bot: [urlparse(page.raw.final_url).path or "/" for page in pages if not robots.can_fetch(bot, page.raw.final_url)]
        for bot in GOOGLE_BOTS
    }
    evidence_url = f"{get_origin(url)}/robots.txt"
    for bot, paths in blocked.items():
        if paths:
            found = f"robots.txt blochează {bot} pentru {', '.join(paths)}."
            return get_check_result("T02", "fail", Evidence(found=found, url=evidence_url), gate=bot == "Googlebot")
    return get_check_result("T02", "pass", Evidence(url=evidence_url))


def get_other_crawlers_check(robots: RobotFileParser, url: str) -> CheckResult:
    """Returns T03: whether robots.txt lets the other AI crawlers read the homepage."""
    blocked = [bot for bot in OTHER_AI_BOTS if not robots.can_fetch(bot, url)]
    status = "pass" if not blocked else "fail" if len(blocked) == len(OTHER_AI_BOTS) else "partial"
    return get_check_result("T03", status, Evidence(found=", ".join(blocked) or None, url=f"{get_origin(url)}/robots.txt"))


def get_raw_content_check(name: str, canonical: CanonicalProfile | None, homepage: FetchedPage) -> CheckResult:
    """Returns T04: whether the name, address and hours are in the raw HTML; an empty shell caps the content."""
    url = homepage.raw.final_url
    is_shell = is_empty_shell(homepage.raw_text)
    if homepage.rendered_text is None:
        if is_shell:
            return get_check_result("T04", "fail", Evidence(found="tot conținutul", url=url), gate=True)
        return get_check_result("T04", "pass", Evidence(url=url))
    street = get_address_parts(canonical.formatted_address).street if canonical and canonical.formatted_address else None
    raw, rendered = homepage.raw_text, homepage.rendered_text
    found_after_render = {
        "numele": get_name_key(name) in get_name_key(rendered) and get_name_key(name) not in get_name_key(raw),
        "adresa": bool(street) and street in normalize_address(rendered) and street not in normalize_address(raw),
        "programul": bool(TIME_RANGE_PATTERN.search(rendered)) and not TIME_RANGE_PATTERN.search(raw),
    }
    js_only = [label for label, only_rendered in found_after_render.items() if only_rendered]
    if not js_only and not is_shell:
        return get_check_result("T04", "pass", Evidence(url=url))
    found = "tot conținutul" if is_shell else ", ".join(js_only)
    return get_check_result("T04", "fail", Evidence(found=found, url=url), gate=is_shell)


def get_structured_data_check(
    name: str, canonical: CanonicalProfile | None, jsonld: list[dict[str, Any]], url: str
) -> CheckResult:
    """Returns T06: LocalBusiness structured data with the name and the address or phone from Google."""
    businesses = [item for item in jsonld if set(get_types(item)) & LOCAL_BUSINESS_TYPES]
    if not businesses:
        return get_check_result(
            "T06", "fail", Evidence(found="Nu am găsit date structurate de tip LocalBusiness pe site.", url=url)
        )
    street = get_address_parts(canonical.formatted_address).street if canonical and canonical.formatted_address else None
    for business in businesses:
        same_name = get_name_key(name) in get_name_key(str(business.get("name", "")))
        address_text = normalize_address(json.dumps(business.get("address", ""), ensure_ascii=False))
        same_place = (bool(street) and street in address_text) or (
            canonical is not None
            and canonical.phone_e164 is not None
            and normalize_phone(str(business.get("telephone", ""))) == canonical.phone_e164
        )
        if same_name and same_place:
            return get_check_result("T06", "pass", Evidence(url=url))
    found = "Datele structurate nu au numele și adresa sau telefonul de pe Google."
    return get_check_result("T06", "partial", Evidence(found=found, url=url))


def get_types(item: dict[str, Any]) -> list[str]:
    """Returns a JSON-LD object's `@type` values as a list."""
    value = item.get("@type", [])
    return [value] if isinstance(value, str) else [entry for entry in value if isinstance(entry, str)]


def get_speed_check(speed: int | None, homepage: FetchedPage) -> CheckResult:
    """Returns T07: PageSpeed mobile performance, or the time to first byte when PageSpeed fails."""
    url = homepage.raw.final_url
    if speed is not None:
        status = "pass" if speed >= 90 else "partial" if speed >= 50 else "fail"
        return get_check_result(
            "T07", status, Evidence(found=f"Scorul de viteză pe telefon e {speed} din 100.", expected="90", url=url)
        )
    seconds = homepage.raw.elapsed_seconds
    status = "pass" if seconds < 0.8 else "partial" if seconds < 1.8 else "fail"
    found = f"Prima pagină a răspuns în {seconds:.1f} secunde.".replace(".", ",", 1)
    return get_check_result("T07", status, Evidence(found=found, expected="0,8 secunde", url=url))
