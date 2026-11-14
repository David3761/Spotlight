"""Writes the fix texts for open `generate` problems and holds the helpers the other fix modules share."""

from app import cache
from app.fixes.schemas import GeneratedText, GeneratedTextDraft, Tone
from app.llm.client import PROMPTS_DIR, json_call
from app.models import Facts, Problem, Report, ScanInputs
from app.services.resolution import load_facts, load_inputs, load_report

TONE_INSTRUCTIONS: dict[Tone, str] = {
    "prietenos": "Ton prietenos și cald, ca și cum proprietarul vorbește direct cu clienții.",
    "profesionist": "Ton profesionist și clar, fără exclamații și fără expresii de vânzare.",
    "scurt": "Ton scurt și direct: cât mai puține cuvinte, doar esențialul.",
}
"""The instruction added to the prompt for each tone."""


async def get_generated_text(
    scan_id: str, check_id: str, tone: Tone, variant: int
) -> GeneratedText | None:
    """Returns the generated text for an open `generate` problem, or `None` when the check is not one."""
    report = load_report(scan_id)
    problem = next(
        (
            candidate
            for candidate in get_open_problems(report)
            if candidate.check_id == check_id and candidate.fix_type == "generate"
        ),
        None,
    )
    if problem is None:
        return None

    cache_key = [scan_id, check_id, tone, str(variant)]
    cached = cache.get(cache_key)
    if cached is not None:
        return GeneratedText(**cached)

    inputs = load_inputs(scan_id)
    prompt = get_text_prompt(problem, tone, variant, load_facts(scan_id), inputs)
    max_chars = problem.fix.max_chars
    draft = await json_call(prompt, GeneratedTextDraft, tier="smart")
    if max_chars is not None and len(draft.text) > max_chars:
        stricter_prompt = (
            f"{prompt}\n\nRăspunsul anterior a avut {len(draft.text)} de caractere, "
            f"iar limita este {max_chars}. Scrie din nou, mai scurt, "
            f"sub {max_chars} de caractere, cu aceleași fapte esențiale."
        )
        draft = await json_call(stricter_prompt, GeneratedTextDraft, tier="smart")

    generated = GeneratedText(
        check_id=check_id,
        tone=tone,
        variant=variant,
        text=draft.text,
        included_ro=draft.included_ro,
        max_chars=max_chars,
    )
    cache.set(cache_key, generated.model_dump())
    return generated


def get_text_prompt(
    problem: Problem, tone: Tone, variant: int, facts: Facts, inputs: ScanInputs
) -> str:
    """Returns the filled prompt for a problem, from its own prompt file or the generic one."""
    prompt_name = f"fix_{problem.check_id}"
    template = get_prompt(
        prompt_name if (PROMPTS_DIR / f"{prompt_name}.md").exists() else "fix_generic"
    )
    variant_instruction = (
        f"Aceasta e varianta {variant + 1}: folosește alte cuvinte și altă structură "
        "decât în varianta obișnuită, cu aceleași fapte."
        if variant > 0
        else ""
    )
    fix = problem.fix
    problem_lines = [f"- Problema: {problem.title_ro}", f"- De ce contează: {problem.why_ro}"]
    if fix.evidence_ro:
        problem_lines.append(f"- Ce am găsit: {fix.evidence_ro}")
    if fix.where_ro:
        problem_lines.append(f"- Unde se pune textul: {fix.where_ro}")
    return template.format(
        facts=get_facts_text(facts, inputs.business_type_label_ro),
        problem="\n".join(problem_lines),
        tone_instruction=TONE_INSTRUCTIONS[tone],
        variant_instruction=variant_instruction,
        limit_instruction=(
            f"Maximum {fix.max_chars} de caractere, spații incluse." if fix.max_chars else ""
        ),
    )


def get_prompt(name: str) -> str:
    """Returns the text of the prompt file with the given name, without extension."""
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def get_facts_text(facts: Facts, type_label_ro: str) -> str:
    """Returns the known facts as Romanian bullet lines, leaving out every missing fact."""
    website_facts = facts.website_facts
    lines = [
        f"- Nume: {facts.name}",
        f"- Tip de afacere: {type_label_ro}",
        f"- Oraș: {facts.city}",
        f"- Cartier: {facts.neighborhood}",
    ]
    optional_lines = [
        ("Adresă", facts.address),
        ("Telefon", facts.phone),
        ("Site", facts.website),
        ("Program", "; ".join(facts.hours_ro)),
        ("Program special", "; ".join(facts.special_hours_ro)),
        ("Facilități", ", ".join(facts.attributes_ro)),
        ("Instagram", f"@{facts.instagram_handle}" if facts.instagram_handle else None),
        ("Apare și pe", ", ".join(facts.platforms_ro)),
    ]
    if website_facts is not None:
        optional_lines += [
            ("Descriere de pe site", website_facts.what_it_is),
            ("Ce servește", ", ".join(website_facts.menu_items_or_services)),
        ]
    lines += [f"- {label}: {value}" for label, value in optional_lines if value]
    return "\n".join(lines)


def get_open_problems(report: Report) -> list[Problem]:
    """Returns every open problem in the report, in chapter order."""
    return [problem for chapter in report.chapters for problem in chapter.problems]
