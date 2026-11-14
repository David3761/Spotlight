"""3.7 Training-data probe → `cunoaste`: what Gemini already knows about the business without searching (K01–K03)."""

import asyncio

from pydantic import BaseModel

from app.llm.client import PROMPTS_DIR, json_call, text_call
from app.models import ScanInputs
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.normalize import get_name_key
from app.pipeline.romanian import TYPE_NOUNS
from app.pipeline.scoring import get_check_result
from app.pipeline.types import CheckResult, Evidence

PROBE_CHECK_IDS = ["K01", "K02", "K03"]
"""The training-data checks."""

PROBE_RUNS = 3
"""How many times each probe question is asked."""

PROBE_QUESTION_COUNT = 6
"""How many questions the probe asks Gemini: two questions, three times each."""

KNOWN_MIN_RUNS = 2
"""In how many of the runs Gemini must describe the business for K01."""


class ProbeVerdict(BaseModel):
    """The L7 judge's reading of the probe answers against Google's facts."""

    knows_business: list[bool]
    correct_type_and_area: bool
    wrong_facts: list[str]


async def collect_training_probe(inputs: ScanInputs, canonical: CanonicalProfile | None) -> list[CheckResult]:
    """Returns K01–K03: two questions asked three times each with no tools, read by one judge call.

    K01 passes when Gemini describes the business in at least two of the three „Ce știi despre” answers,
    or names it in any of the recommendations.
    """
    name = canonical.name if canonical else inputs.business_name
    about_question = f"Ce știi despre {name} din {inputs.neighborhood}, {inputs.city}?"
    recommend_question = f"Recomandă câteva {TYPE_NOUNS[inputs.business_type].plural} din {inputs.neighborhood}."
    about_answers, recommend_answers = await asyncio.gather(get_answers(about_question), get_answers(recommend_question))
    verdict = await json_call(get_judge_prompt(inputs, canonical, name, about_answers, recommend_answers), ProbeVerdict)
    known_runs = sum(verdict.knows_business[:PROBE_RUNS])
    name_key = get_name_key(name)
    is_recommended = bool(name_key) and any(f" {name_key} " in f" {get_name_key(answer)} " for answer in recommend_answers)
    knows = known_runs >= KNOWN_MIN_RUNS or is_recommended
    known_found = f"Te descrie în {known_runs} din {PROBE_RUNS} răspunsuri" + (
        " și te recomandă când întrebăm de locuri din cartier." if is_recommended else "."
    )
    return [
        get_check_result("K01", "pass" if knows else "fail", Evidence(found=known_found)),
        get_check_result("K02", "pass" if knows and verdict.correct_type_and_area else "fail"),
        get_check_result(
            "K03",
            "fail" if verdict.wrong_facts else "pass",
            Evidence(found="; ".join(verdict.wrong_facts) or None),
        ),
    ]


async def get_answers(question: str) -> list[str]:
    """Returns Gemini's answers to the same question asked three times, on the fast model with no tools."""
    return list(await asyncio.gather(*(text_call(question, "fast", run=run) for run in range(PROBE_RUNS))))


def get_judge_prompt(
    inputs: ScanInputs,
    canonical: CanonicalProfile | None,
    name: str,
    about_answers: list[str],
    recommend_answers: list[str],
) -> str:
    """Returns the L7 judge prompt: Google's facts, then the six answers."""
    facts = {
        "Adresa": canonical.formatted_address if canonical else None,
        "Telefon": canonical.national_phone if canonical else None,
        "Program": "; ".join(canonical.hours_ro) if canonical and canonical.hours_ro else None,
        "Site": (canonical.website if canonical else None) or inputs.website_url,
    }
    return (
        (PROMPTS_DIR / "training_judge.md")
        .read_text(encoding="utf-8")
        .format(
            name=name,
            type_label=inputs.business_type_label_ro.lower(),
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            facts="\n".join(f"- {label}: {value}" for label, value in facts.items() if value),
            about_answers="\n\n".join(f"#### Răspunsul {number}\n{answer}" for number, answer in enumerate(about_answers, 1)),
            recommend_answers="\n\n".join(
                f"#### Răspunsul {number}\n{answer}" for number, answer in enumerate(recommend_answers, 1)
            ),
        )
    )
