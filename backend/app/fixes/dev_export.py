"""Builds the developer export: a Markdown document with the open technical problems and their exact fixes."""

import json

from app.fixes.generate import get_open_problems
from app.fixes.schemas import DevExport
from app.models import Facts, Problem
from app.services.resolution import load_facts, load_report

SITE_WITHOUT_WEBSITE = "adresa-site-ului"
"""The site address written in the verification commands when the business has no website."""

GOOGLE_CRAWLERS = ["Googlebot", "Google-Extended"]
"""The crawlers check T02 asks the site to allow."""

AI_CRAWLERS = ["OAI-SearchBot", "GPTBot", "PerplexityBot", "ClaudeBot"]
"""The crawlers check T03 asks the site to allow."""

VERIFICATION_BY_CHECK = {
    "T01": "Deschide {site} în browser: adresa începe cu `https://` și pagina se încarcă fără erori. Din terminal, `curl -sI {site}` răspunde `200`.",
    "T02": "`curl -s {site}/robots.txt` nu conține `Disallow: /` pentru Googlebot sau Google-Extended. `curl -A 'Googlebot' -sI {site}` răspunde `200`.",
    "T03": "`curl -s {site}/robots.txt` nu blochează cei patru crawleri. `curl -A 'GPTBot' -sI {site}` răspunde `200`, nu `403`.",
    "T04": "`curl -s {site}` conține în HTML textul paginii (adresa, programul, meniul), nu doar un element gol în care se încarcă totul cu JavaScript.",
    "T05": "`curl -sI {site}/sitemap.xml` răspunde `200`, iar `{site}/robots.txt` conține linia `Sitemap:` cu adresa lui.",
    "T06": "Lipește pagina în Rich Results Test (search.google.com/test/rich-results): afacerea apare ca „Local business” fără erori.",
    "T07": "Rulează {site} în PageSpeed Insights (pagespeed.web.dev), pe mobil: timpul de încărcare scade față de analiza inițială.",
    "T08": '`curl -s {site}` conține `<meta name="viewport" content="width=device-width, initial-scale=1">`.',
}
"""How to verify each technical check, with `{site}` standing for the site address."""

GENERIC_VERIFICATION = "După modificare, cere confirmarea și rulează din nou analiza: problema dispare din listă."
"""How to verify a check that has no specific instructions."""

DEVELOPER_MESSAGE = (
    "Salut! Îți trimit instrucțiunile tehnice pentru site-ul {name}: ce trebuie schimbat, "
    "cu textele exacte (robots.txt, date structurate) și cum verifici fiecare modificare. "
    "Te rog să le aplici și să-mi spui când sunt gata. Mulțumesc mult!"
)
"""The note to the person who builds the website."""


def get_dev_export(scan_id: str) -> DevExport:
    """Returns the Markdown document for every open developer problem, plus the note for the developer."""
    report = load_report(scan_id)
    facts = load_facts(scan_id)
    problems = [problem for problem in get_open_problems(report) if problem.fix_type == "dev_export"]
    site = facts.website or SITE_WITHOUT_WEBSITE

    blocks = [f"# Instrucțiuni tehnice pentru {facts.name}"]
    if problems:
        blocks += [get_problem_block(number, problem, facts, site) for number, problem in enumerate(problems, 1)]
    else:
        blocks.append("Nu sunt probleme tehnice deschise.")

    check_ids = {problem.check_id for problem in problems}
    crawlers = (GOOGLE_CRAWLERS if "T02" in check_ids else []) + (AI_CRAWLERS if "T03" in check_ids else [])
    if crawlers:
        robots_lines = "\n\n".join(f"User-agent: {crawler}\nAllow: /" for crawler in crawlers)
        blocks.append(
            f"## Linii pentru robots.txt\n\nAdaugă în `robots.txt`, la rădăcina site-ului:\n\n```text\n{robots_lines}\n```"
        )
    if "T06" in check_ids:
        blocks.append(
            "## Date structurate (JSON-LD)\n\n"
            "Pune în `<head>` al paginii principale, completând ce lipsește:\n\n"
            f'```html\n<script type="application/ld+json">\n{get_json_ld(facts, report.business.type)}\n</script>\n```'
        )
    return DevExport(
        markdown="\n\n".join(blocks) + "\n",
        message_ro=DEVELOPER_MESSAGE.format(name=facts.name),
    )


def get_problem_block(number: int, problem: Problem, facts: Facts, site: str) -> str:
    """Returns the Markdown section for one problem: what is wrong, evidence, steps and verification."""
    fix = problem.fix
    lines = [f"## {number}. {problem.title_ro}", "", f"**Ce nu e în regulă:** {problem.title_ro}"]
    if fix.evidence_ro:
        lines.append(f"\n**Ce am găsit:** {fix.evidence_ro}")
    if fix.steps_ro:
        lines.append("\n**Cum se rezolvă:**\n")
        lines += [f"{step_number}. {step}" for step_number, step in enumerate(fix.steps_ro, 1)]
    verification = VERIFICATION_BY_CHECK.get(problem.check_id, GENERIC_VERIFICATION)
    lines.append(f"\n**Cum verifici:** {verification.format(site=site)}")
    return "\n".join(lines)


def get_json_ld(facts: Facts, business_type: str) -> str:
    """Returns the `LocalBusiness` JSON-LD for the business, with only the fields that are known."""
    same_as = [
        link
        for link in (
            f"https://www.instagram.com/{facts.instagram_handle}" if facts.instagram_handle else None,
            facts.tiktok_url,
        )
        if link
    ]
    address = {"@type": "PostalAddress", "addressLocality": facts.city}
    if facts.address:
        address["streetAddress"] = facts.address
    snippet = {
        "@context": "https://schema.org",
        "@type": "CafeOrCoffeeShop" if business_type == "cafenea" else "LocalBusiness",
        "name": facts.name,
        "address": address,
        "telephone": facts.phone,
        "url": facts.website,
        "hasMap": facts.google_maps_uri,
        "sameAs": same_as,
    }
    known = {key: value for key, value in snippet.items() if value}
    return json.dumps(known, ensure_ascii=False, indent=2)
