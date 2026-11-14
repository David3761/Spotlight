"""Builds the info page from the business facts, with the language model writing only the free text."""

from html import escape
from urllib.parse import urlparse

from app import cache
from app.fixes.generate import get_facts_text, get_prompt
from app.fixes.schemas import InfoPage, InfoPageDraft
from app.llm.client import json_call
from app.models import Facts, FaqItem
from app.services.resolution import load_facts

MAX_FAQ_QUESTIONS = 5
"""The most questions the page answers."""

HOLIDAY_PLACEHOLDER = "de completat"
"""The text shown where the holiday hours are missing."""

PHONE_PLACEHOLDER = "numărul tău"
"""The text shown where the phone number is missing."""


async def get_info_page(scan_id: str) -> InfoPage:
    """Returns the info page for a scan, written once and then served from the cache."""
    facts = load_facts(scan_id)
    cache_key = ["info-page", scan_id]
    cached = cache.get(cache_key)
    if cached is not None:
        return InfoPage(**cached)

    suggested_url = get_suggested_url(facts)
    questions = get_faq_questions(facts)
    prompt = get_prompt("fix_info_page").format(
        facts=get_facts_text(facts, facts.type_label_ro),
        suggested_url=suggested_url or "afacerea nu are încă site",
        placement_request=(
            "o rogi să o pună pe site la adresa propusă, cu link din meniu"
            if suggested_url
            else "o rogi să facă un site simplu pornind de la ea, pentru că afacerea nu are încă site"
        ),
        questions="\n".join(f"{number}. {question}" for number, question in enumerate(questions, 1)),
    )
    draft = await json_call(prompt, InfoPageDraft, tier="smart")

    holiday_hours = "; ".join(facts.special_hours_ro) or None
    to_fill = [
        field
        for field, value in (("holiday_hours", holiday_hours), ("phone", facts.phone))
        if value is None
    ]
    page = InfoPage(
        suggested_url=suggested_url,
        title=facts.name,
        subtitle=draft.subtitle,
        description=draft.description,
        address=facts.address,
        area_note=(
            f"Servim clienți din {facts.neighborhood} și din cartierele din jur"
            if facts.neighborhood
            else None
        ),
        hours=facts.hours_ro,
        holiday_hours=holiday_hours,
        phone=facts.phone,
        instagram=f"@{facts.instagram_handle}" if facts.instagram_handle else None,
        also_on=(["Google Maps"] if facts.google_maps_uri else []) + facts.platforms_ro,
        menu=facts.website_facts.menu_items_or_services if facts.website_facts else [],
        faq=[
            FaqItem(q=question, a=answer)
            for question, answer in zip(questions, draft.faq_answers, strict=False)
        ],
        to_fill=to_fill,
        message_ro=draft.message_ro,
        html="",
    )
    page.html = get_html(page)
    cache.set(cache_key, page.model_dump())
    return page


def get_suggested_url(facts: Facts) -> str | None:
    """Returns the website's domain followed by `/despre`, or `None` when there is no website."""
    if not facts.website:
        return None
    website = facts.website if "//" in facts.website else f"//{facts.website}"
    domain = urlparse(website).netloc.removeprefix("www.")
    return f"{domain}/despre"


def get_faq_questions(facts: Facts) -> list[str]:
    """Returns the questions the page answers: the ones the site already has, then address and hours."""
    questions = [item.q for item in facts.website_facts.faq_items] if facts.website_facts else []
    if facts.address:
        questions.append("Unde vă găsim?")
    if facts.hours_ro:
        questions.append("Care este programul?")
    return questions[:MAX_FAQ_QUESTIONS]


def get_html(page: InfoPage) -> str:
    """Returns the page as a standalone HTML document with every value escaped."""
    sections = []

    place_lines = [escape(line) for line in (page.address, page.area_note) if line]
    if place_lines:
        sections.append(("Adresă și zonă", place_lines))

    hours_lines = [escape(line) for line in page.hours]
    holiday = (
        escape(page.holiday_hours)
        if page.holiday_hours
        else f"<mark>{HOLIDAY_PLACEHOLDER}</mark>"
    )
    hours_lines.append(f"Sărbători: {holiday}")
    sections.append(("Program", hours_lines))

    phone = escape(page.phone) if page.phone else f"<mark>{PHONE_PLACEHOLDER}</mark>"
    contact_lines = [f"Telefon: {phone}"]
    if page.instagram:
        contact_lines.append(f"Instagram: {escape(page.instagram)}")
    sections.append(("Contact", contact_lines))

    if page.also_on:
        sections.append(("Ne găsești și pe", [escape(", ".join(page.also_on))]))
    if page.menu:
        sections.append(("Ce servim", [escape(item) for item in page.menu]))

    section_html = "\n".join(
        f"<section><h2>{heading}</h2>"
        + "".join(f"<p>{line}</p>" for line in lines)
        + "</section>"
        for heading, lines in sections
    )
    faq_html = "".join(
        f"<dt>{escape(item.q)}</dt><dd>{escape(item.a)}</dd>" for item in page.faq
    )
    faq_section = f"<section><h2>Întrebări frecvente</h2><dl>{faq_html}</dl></section>" if faq_html else ""
    return f"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page.title)}</title>
<meta name="description" content="{escape(page.description, quote=True)}">
<style>
body{{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:24px 16px;color:#0F172A;line-height:1.6}}
h1{{margin-bottom:4px}}
h2{{font-size:1.1rem;margin:24px 0 8px}}
p{{margin:4px 0}}
dt{{font-weight:700;margin-top:12px}}
dd{{margin:2px 0 0}}
mark{{background:#FEF08A}}
.subtitle{{color:#475569;margin:0 0 16px}}
</style>
</head>
<body>
<main>
<h1>{escape(page.title)}</h1>
<p class="subtitle">{escape(page.subtitle)}</p>
<p>{escape(page.description)}</p>
{section_html}
{faq_section}
</main>
</body>
</html>
"""
