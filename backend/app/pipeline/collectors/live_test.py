"""3.8 Live Gemini test → the `gemini` block: 12 customer questions, each asked 3 times with Maps grounding."""

import asyncio
import logging
import statistics
from collections import Counter
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel

from app.llm.client import PROMPTS_DIR, GroundedAnswer, grounded_call, json_call
from app.models import GeminiBlock, GeminiGroup, GeminiPrompt, ScanInputs, Source, TopCompetitor
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.normalize import get_name_key
from app.pipeline.places_api import places_request
from app.pipeline.romanian import TYPE_NOUNS, get_list_phrase
from app.pipeline.scoring import GEMINI_WEIGHT, get_gemini_score

logger = logging.getLogger(__name__)

GroupId = Literal["general", "cartier", "situatii"]
"""The three groups of customer questions."""

GROUPS: list[tuple[GroupId, str, str]] = [
    ("general", "General", "Întrebări despre tot orașul"),
    ("cartier", "Cartier", "Întrebări despre zona ta"),
    ("situatii", "Situații", "Ce caută oamenii, nu unde"),
]
"""Each group's ID, name and description, in display order."""

QUESTIONS_PER_GROUP = 4
"""How many questions each group has."""

RUNS = 3
"""How many times each question is asked; Gemini's answers vary between runs."""

ANSWERS_TIMEOUT_SECONDS = 60
"""How long the 36 answers may take; the test is scored on the answers that came back by then."""

EXCERPT_CHARACTERS = 300
"""How much of an answer the Gemini screen shows."""

MAX_SOURCES = 5
"""How many sources the Gemini screen shows under a question."""

TOP_COMPETITOR_COUNT = 3
"""How many rivals the dashboard and comparison show."""

MIN_NAME_KEY_LENGTH = 4
"""Names shorter than this are too ambiguous to look for in an answer's text."""


class QuestionPlan(BaseModel):
    """The L5 output: four customer questions per group."""

    general: list[str]
    cartier: list[str]
    situatii: list[str]


class FactsVerdict(BaseModel):
    """The L6 output: statements about the business that contradict its Google profile."""

    wrong_facts: list[str]


class NamedPlace(BaseModel):
    """A business an answer named, with its Google place ID when Maps grounding cited it."""

    name: str
    place_id: str | None


class RunResult(BaseModel):
    """One answer to one question, parsed."""

    text: str
    mentioned: bool
    position: int | None
    others: list[NamedPlace]
    sources: list[Source]


class LiveTestResult(BaseModel):
    """The live test's Gemini block, plus the rivals it found, for the comparison."""

    block: GeminiBlock
    rivals: list[NamedPlace]


async def collect_live_test(
    inputs: ScanInputs, canonical: CanonicalProfile | None, round_number: int = 0
) -> LiveTestResult | None:
    """Returns the live test's result, or `None` when no answer came back.

    A re-test passes a new `round_number`, so none of its answers come from the cache.
    """
    plan = await get_question_plan(inputs, canonical)
    location = await get_location(inputs, canonical)
    questions = [(group_id, question) for group_id, _, _ in GROUPS for question in getattr(plan, group_id)]
    answers = await get_answers([question for _, question in questions], location, round_number)
    answered: list[tuple[GroupId, str, list[RunResult]]] = []
    for index, (group_id, question) in enumerate(questions):
        question_answers = answers[index * RUNS : (index + 1) * RUNS]
        runs = [get_run_result(answer, inputs, canonical) for answer in question_answers if answer]
        if runs:
            answered.append((group_id, question, runs))
    if not answered:
        return None
    prompts = [get_question_result(question, runs) for _, question, runs in answered]
    positions = [get_question_position(prompt, runs) for prompt, (_, _, runs) in zip(prompts, answered, strict=True)]
    facts_ok = await get_facts_ok(canonical, [run for _, _, runs in answered for run in runs if run.mentioned])
    groups = [
        get_group(
            group_id,
            name_ro,
            desc_ro,
            [prompt for prompt, (group, _, _) in zip(prompts, answered, strict=True) if group == group_id],
        )
        for group_id, name_ro, desc_ro in GROUPS
    ]
    rivals = get_top_rivals([runs for _, _, runs in answered])
    block = GeminiBlock(
        status="complete",
        score=get_gemini_score(positions, facts_ok),
        weight=GEMINI_WEIGHT,
        mentioned=sum(1 for prompt in prompts if prompt.mentioned),
        total=len(prompts),
        last_checked=datetime.now(UTC).isoformat(),
        top_competitors=[TopCompetitor(name=rival.name, place_id=rival.place_id, mentions=count) for rival, count in rivals],
        groups=groups,
    )
    return LiveTestResult(block=block, rivals=[rival for rival, _ in rivals])


async def get_question_plan(inputs: ScanInputs, canonical: CanonicalProfile | None) -> QuestionPlan:
    """Returns the 12 customer questions (L5), topped up from templates when the model gives too few or fails."""
    nouns = TYPE_NOUNS[inputs.business_type]
    fallback = get_fallback_plan(inputs)
    attributes = get_list_phrase([label.lower() for label in canonical.attributes_ro]) if canonical else ""
    prompt = (
        (PROMPTS_DIR / "live_test_questions.md")
        .read_text(encoding="utf-8")
        .format(
            type_label=inputs.business_type_label_ro.lower(),
            type_noun=nouns.singular,
            neighborhood=inputs.neighborhood,
            city=inputs.city,
            attributes=attributes or "nimic în plus",
        )
    )
    try:
        plan = await json_call(prompt, QuestionPlan)
    except Exception:
        logger.exception("Question generation failed; using the template questions")
        return fallback
    return QuestionPlan(
        general=get_group_questions(plan.general, fallback.general),
        cartier=get_group_questions(plan.cartier, fallback.cartier),
        situatii=get_group_questions(plan.situatii, fallback.situatii),
    )


def get_group_questions(generated: list[str], fallback: list[str]) -> list[str]:
    """Returns a group's four questions: the generated ones first, topped up from the templates."""
    questions = [question.strip() for question in generated if question.strip()][:QUESTIONS_PER_GROUP]
    return questions + fallback[len(questions) : QUESTIONS_PER_GROUP]


def get_fallback_plan(inputs: ScanInputs) -> QuestionPlan:
    """Returns template questions in the plural, which reads right for every business type („cele mai bune restaurante”)."""
    plural = TYPE_NOUNS[inputs.business_type].plural
    city, area = inputs.city, inputs.neighborhood
    return QuestionPlan(
        general=[
            f"cele mai bune {plural} din {city}",
            f"{plural} recomandate în {city}",
            f"{plural} bune în {city}",
            f"top {plural} {city}",
        ],
        cartier=[
            f"{plural} în {area}",
            f"{plural} aproape de {area}, {city}",
            f"{plural} deschise duminica în {area}",
            f"cele mai bune {plural} din {area}",
        ],
        situatii=[
            f"{plural} unde pot lucra cu laptopul în {city}",
            f"{plural} liniștite pentru o întâlnire în {city}",
            f"{plural} cu terasă în {city}",
            f"{plural} unde pot veni cu câinele în {city}",
        ],
    )


async def get_location(inputs: ScanInputs, canonical: CanonicalProfile | None) -> tuple[float, float] | None:
    """Returns where the customer asks from: the business, or the neighbourhood's centre when it has no profile."""
    if canonical and canonical.lat is not None and canonical.lng is not None:
        return canonical.lat, canonical.lng
    try:
        data = await places_request(
            "POST", "places:searchText", "places.location", {"textQuery": f"{inputs.neighborhood}, {inputs.city}", "pageSize": 1}
        )
    except Exception:
        logger.exception("Neighbourhood lookup failed")
        return None
    places = data.get("places", [])
    location = places[0].get("location") if places else None
    return (location["latitude"], location["longitude"]) if location else None


async def get_answers(
    questions: list[str], location: tuple[float, float] | None, round_number: int
) -> list[GroundedAnswer | None]:
    """Returns every question's three answers in order; one that fails or isn't back within the time limit is `None`."""
    tasks = [
        asyncio.create_task(get_answer(question, location, round_number * RUNS + run))
        for question in questions
        for run in range(RUNS)
    ]
    try:
        done, _ = await asyncio.wait(tasks, timeout=ANSWERS_TIMEOUT_SECONDS)
    finally:
        for task in tasks:
            task.cancel()
    return [task.result() if task in done else None for task in tasks]


async def get_answer(question: str, location: tuple[float, float] | None, run: int) -> GroundedAnswer | None:
    """Returns one Maps-grounded answer to a customer question, or `None` when the call fails."""
    lat, lng = location if location else (None, None)
    try:
        return await grounded_call(question, "maps", lat, lng, run=run)
    except Exception:
        logger.exception("Grounded call failed for %r", question)
        return None


def get_run_result(answer: GroundedAnswer, inputs: ScanInputs, canonical: CanonicalProfile | None) -> RunResult:
    """Returns whether an answer named the business, at which position, and who else it named."""
    text_key = f" {get_name_key(answer.text)} "
    target_id = canonical.place_id if canonical else None
    target_keys = {get_name_key(name) for name in (canonical.name if canonical else "", inputs.business_name)}
    target_keys = {key for key in target_keys if len(key) >= MIN_NAME_KEY_LENGTH}
    cited = [source for source in answer.sources if source.kind == "maps"]
    cited_target = any(target_id and source.place_id == target_id for source in cited)
    named_target = [text_key.find(f" {key} ") for key in target_keys if f" {key} " in text_key]
    others = get_unique_places(
        [
            NamedPlace(name=source.title, place_id=source.place_id)
            for source in cited
            if source.place_id != target_id and not any(f" {key} " in f" {get_name_key(source.title)} " for key in target_keys)
        ]
    )
    mentioned = cited_target or bool(named_target)
    position = None
    if mentioned:
        target_index = min(named_target, default=len(text_key))
        earlier = [other for other in others if 0 <= text_key.find(f" {get_name_key(other.name)} ") < target_index]
        position = len(earlier) + 1
    sources = [Source(title=source.title, uri=source.uri, kind="maps") for source in cited]
    return RunResult(text=answer.text, mentioned=mentioned, position=position, others=others, sources=sources)


def get_unique_places(places: list[NamedPlace]) -> list[NamedPlace]:
    """Returns one entry per business name, in first-seen order, keeping the one with a Google place ID when there is one."""
    unique: dict[str, NamedPlace] = {}
    for place in places:
        key = get_name_key(place.name)
        if key not in unique or (place.place_id and not unique[key].place_id):
            unique[key] = place
    return list(unique.values())


def get_question_result(question: str, runs: list[RunResult]) -> GeminiPrompt:
    """Returns one question's result: named when the business appears in most of its runs."""
    runs_mentioned = sum(1 for run in runs if run.mentioned)
    others = Counter(other.name for run in runs for other in run.others)
    excerpt_run = next((run for run in runs if run.mentioned), runs[0])
    sources: dict[str, Source] = {}
    for run in runs:
        for source in run.sources:
            sources.setdefault(get_name_key(source.title), source)
    return GeminiPrompt(
        text=question,
        mentioned=runs_mentioned * 2 > len(runs),
        runs_mentioned=runs_mentioned,
        runs=len(runs),
        others=[name for name, _ in others.most_common(TOP_COMPETITOR_COUNT)],
        answer_excerpt=get_excerpt(excerpt_run.text),
        sources=list(sources.values())[:MAX_SOURCES],
    )


def get_excerpt(text: str) -> str:
    """Returns the start of an answer, cut at a word boundary."""
    flat = " ".join(text.split())
    if len(flat) <= EXCERPT_CHARACTERS:
        return flat
    return flat[:EXCERPT_CHARACTERS].rsplit(" ", 1)[0] + "…"


def get_question_position(prompt: GeminiPrompt, runs: list[RunResult]) -> int | None:
    """Returns the business's median position in a question that named it, or `None` when the question didn't."""
    positions = [run.position for run in runs if run.mentioned and run.position is not None]
    if not prompt.mentioned or not positions:
        return None
    return round(statistics.median(positions))


async def get_facts_ok(canonical: CanonicalProfile | None, mentioning_runs: list[RunResult]) -> bool | None:
    """Returns whether the answers that named the business got its address and hours right (L6); `None` when unknown."""
    if canonical is None or not mentioning_runs:
        return None
    prompt = (
        (PROMPTS_DIR / "live_test_facts.md")
        .read_text(encoding="utf-8")
        .format(
            name=canonical.name,
            address=canonical.formatted_address or "necunoscută",
            hours="; ".join(canonical.hours_ro) or "necunoscut",
            answers="\n\n---\n\n".join(run.text[:1500] for run in mentioning_runs[:8]),
        )
    )
    try:
        verdict = await json_call(prompt, FactsVerdict)
    except Exception:
        logger.exception("Facts check failed")
        return None
    return not verdict.wrong_facts


def get_group(group_id: GroupId, name_ro: str, desc_ro: str, prompts: list[GeminiPrompt]) -> GeminiGroup:
    """Returns one group of answered questions with how many of them named the business."""
    return GeminiGroup(
        id=group_id,
        name_ro=name_ro,
        desc_ro=desc_ro,
        mentioned=sum(1 for prompt in prompts if prompt.mentioned),
        total=len(prompts),
        prompts=prompts,
    )


def get_top_rivals(runs_by_question: list[list[RunResult]]) -> list[tuple[NamedPlace, int]]:
    """Returns the businesses Gemini named in the most questions, with how many questions named each."""
    counts: Counter[str] = Counter()
    places: list[NamedPlace] = []
    for runs in runs_by_question:
        named = get_unique_places([other for run in runs for other in run.others])
        counts.update(get_name_key(place.name) for place in named)
        places += named
    by_key = {get_name_key(place.name): place for place in get_unique_places(places)}
    return [(by_key[key], count) for key, count in counts.most_common(TOP_COMPETITOR_COUNT)]
