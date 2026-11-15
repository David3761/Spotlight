"""The AI-led onboarding: Gemini reads each owner message and writes the next question; the code checks every value."""

import json
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel

from app.errors import ApiError
from app.llm.client import PROMPTS_DIR, json_call
from app.models import (
    BusinessType,
    OnboardingAnswers,
    OnboardingField,
    OnboardingMessage,
    OnboardingTurn,
    PlaceCandidate,
    Platform,
    PostRecency,
    YesNoUnknown,
)
from app.pipeline.normalize import get_domain, get_instagram_handle, is_on_host
from app.pipeline.resolve import resolve_link, search_places

logger = logging.getLogger(__name__)


class OnboardingFacts(BaseModel):
    """The facts Gemini found in the owner's newest message; `None` where the message says nothing about one."""

    business_name: str | None
    business_type: BusinessType | None
    business_type_label_ro: str | None
    city: str | None
    neighborhood: str | None
    has_website: bool | None
    website_url: str | None
    maps_url: str | None
    picked_place: int | None
    google_choice: Literal["none", "later"] | None
    profile_claimed: YesNoUnknown | None
    has_google_description: YesNoUnknown | None
    last_google_post: PostRecency | None
    has_social: bool | None
    instagram: str | None
    tiktok: str | None
    last_social_post: PostRecency | None
    platforms: list[Platform] | None


class OnboardingReply(BaseModel):
    """Gemini's reading of the owner's newest message, the answer it asks for next and its message."""

    facts: OnboardingFacts
    asks: OnboardingField | None
    reply_ro: str


LinkProblem = Literal["unreadable", "unavailable"]
"""Why a pasted Google Maps link gave no place: it can't be read, or Google Maps didn't answer."""

TYPE_LABELS_RO: dict[BusinessType, str | None] = {
    "cafenea": "Cafenea",
    "restaurant": "Restaurant",
    "bar": "Bar",
    "salon": "Salon",
    "hotel": "Hotel",
    "magazin": "Magazin",
    "altceva": None,
}
"""The label of each business type when the owner gave no words of their own; „altceva” needs the owner's."""

QUESTIONS_RO: dict[OnboardingField, str] = {
    "business_name": "Cum se numește afacerea ta?",
    "business_type": "Ce fel de afacere ai?",
    "city": "În ce oraș te găsesc clienții?",
    "neighborhood": "Și în ce cartier sau zonă?",
    "website": "Ai un site web? Dacă da, scrie-mi adresa.",
    "google_profile": "Lipește linkul afacerii tale de pe Google Maps sau spune-mi dacă nu ai profil Google.",
    "profile_claimed": "Ai revendicat profilul Google?",
    "has_google_description": "Ai o descriere în profilul Google?",
    "last_google_post": "Când ai postat ultima dată pe Google?",
    "social": "Ai Instagram sau TikTok? Scrie-mi linkurile sau numele conturilor.",
    "last_social_post": "Când ai postat ultima dată pe rețele?",
    "platforms": "Ultima întrebare! Mai ești și pe alte platforme? Alege tot ce se potrivește.",
}
"""The question for each answer, used when Gemini's reply asks for something else than what is missing first."""

DONE_RO = "Am tot ce-mi trebuie. Apasă „Gata, analizează afacerea” și încep analiza."
"""The message once every answer is in."""

NO_PLACES_RO = "Nu am găsit afacerea pe Google Maps. Lipește linkul ei de acolo sau spune-mi dacă nu ai profil Google."
"""The Google Maps question when the search found no place."""

LINK_PROBLEMS_RO: dict[LinkProblem, str] = {
    "unreadable": (
        "Nu am putut deschide acest link. În Google Maps, deschide afacerea, apasă „Distribuie” și copiază linkul de acolo."
    ),
    "unavailable": "Google Maps nu răspunde acum, așa că nu am putut verifica linkul. Încearcă din nou peste puțin.",
}
"""The message when a pasted Google Maps link gave no place, while the Google Maps question is the one asked."""

LINK_LATER_RO = "Linkul de Google Maps nu l-am putut verifica, revenim la el puțin mai încolo."
"""The note before the reply when a pasted Google Maps link gave no place before its question comes up."""

PROMPT_MESSAGE_LIMIT = 30
"""The latest messages the prompt shows; the answers carry everything said before them."""

ROLE_LABELS = {"assistant": "Assistant", "user": "Owner"}
"""How each side of the chat is named in the prompt."""

NOT_WEBSITE_HOSTS = ("google.", "goo.gl", "g.page", "facebook.com", "fb.com", "instagram.com", "tiktok.com")
"""Hosts of pages that aren't the business's own website; „google.” covers every country domain."""

NOT_ACCOUNT_NAMES = {"da", "nu", "nimic", "niciunul", "niciuna", "none", "no"}
"""Plain answers that Gemini may leave in an account field but are never an Instagram or TikTok name."""

GOOGLE_REPORT_FIELDS = ("profile_claimed", "has_google_description", "last_google_post")
"""The self-reported answers about the Google profile."""

SELF_REPORT_FIELDS = (*GOOGLE_REPORT_FIELDS, "last_social_post")
"""The facts that are self-reported answers."""


async def get_onboarding_turn(messages: list[OnboardingMessage], answers: OnboardingAnswers) -> OnboardingTurn:
    """Returns the assistant's next message after the owner's newest one, with the answers that message adds."""
    shown_places = await get_places(answers) if answers.google_choice is None else None
    reply = await get_reply(messages, answers, shown_places)
    updated, link_problem = await get_updated_answers(answers, reply.facts, shown_places)
    missing = get_missing_fields(updated)
    asks = missing[0] if missing else None
    places = None
    if asks == "google_profile":
        is_same_search = (answers.business_name, answers.city, answers.neighborhood) == (
            updated.business_name,
            updated.city,
            updated.neighborhood,
        )
        places = shown_places if is_same_search and shown_places is not None else await get_places(updated)
    return OnboardingTurn(
        reply_ro=get_reply_text(reply, asks, places, shown_places, link_problem),
        answers=updated,
        missing=missing,
        candidates=places or [],
    )


async def get_places(answers: OnboardingAnswers) -> list[PlaceCandidate] | None:
    """Returns the Google places that may be the business, or `None` before the location is known or when the search fails."""
    if not (answers.business_name and answers.city and answers.neighborhood):
        return None
    try:
        return await search_places(answers.business_name, answers.city, answers.neighborhood)
    except ApiError:
        logger.warning("Place search failed during onboarding", exc_info=True)
        return None


async def get_reply(
    messages: list[OnboardingMessage], answers: OnboardingAnswers, places: list[PlaceCandidate] | None
) -> OnboardingReply:
    """Returns Gemini's reading of the owner's newest message and its next question; an identical chat is cached."""
    known = {**answers.model_dump(mode="json", exclude={"place"}), "place": answers.place.name if answers.place else None}
    prompt = (
        (PROMPTS_DIR / "onboarding_turn.md")
        .read_text(encoding="utf-8")
        .format(
            answers=json.dumps(known, ensure_ascii=False, indent=2),
            missing=", ".join(get_missing_fields(answers)) or "nothing",
            places=get_places_text(answers, places),
            conversation="\n".join(
                f"{ROLE_LABELS[message.role]}: {message.text}" for message in messages[-PROMPT_MESSAGE_LIMIT:]
            ),
        )
    )
    system = (PROMPTS_DIR / "onboarding_system.md").read_text(encoding="utf-8")
    try:
        return await json_call(prompt, OnboardingReply, tier="smart", system=system)
    except Exception as error:
        logger.warning("Onboarding reply failed", exc_info=True)
        raise ApiError("upstream_error") from error


def get_places_text(answers: OnboardingAnswers, places: list[PlaceCandidate] | None) -> str:
    """Returns what the prompt says about the Google Maps step."""
    if answers.google_choice is not None:
        return "Already answered (see `google_choice` and `place`)."
    if places is None:
        return "Not searched yet: the app searches once it knows the name, the city and the neighbourhood."
    if not places:
        return "The app searched and found no matching place."
    lines = [f"{index}. {place.name}, {place.address}" for index, place in enumerate(places, start=1)]
    return "The app found these places and shows them as cards under your message:\n" + "\n".join(lines)


async def get_updated_answers(
    answers: OnboardingAnswers, facts: OnboardingFacts, shown_places: list[PlaceCandidate] | None
) -> tuple[OnboardingAnswers, LinkProblem | None]:
    """Returns the answers with the newest message's facts checked and added, and why a pasted Maps link gave no place."""
    update: dict[str, Any] = {
        field: value for field in ("business_name", "city", "neighborhood") if (value := get_clean_text(getattr(facts, field)))
    }
    if facts.business_type:
        update["business_type"] = facts.business_type
        label = get_clean_text(facts.business_type_label_ro)
        update["business_type_label_ro"] = label[:1].upper() + label[1:] if label else TYPE_LABELS_RO[facts.business_type]
    update |= get_website_update(facts)
    google_update, link_problem = await get_google_update(answers, facts, shown_places)
    update |= google_update
    update |= get_social_update(facts)
    reported = {field: value for field in SELF_REPORT_FIELDS if (value := getattr(facts, field)) is not None}
    if update.get("google_choice", answers.google_choice) == "none":
        reported |= dict.fromkeys(GOOGLE_REPORT_FIELDS)
    if update.get("has_social", answers.has_social) is False:
        reported["last_social_post"] = None
    update["self_report"] = answers.self_report.model_copy(update=reported)
    if facts.platforms is not None:
        update["platforms"] = list(dict.fromkeys(facts.platforms))
    return answers.model_copy(update=update), link_problem


def get_clean_text(text: str | None) -> str | None:
    """Returns the text with its spaces tidied, or `None` when nothing is left."""
    return " ".join((text or "").split()) or None


def get_website_update(facts: OnboardingFacts) -> dict[str, Any]:
    """Returns the website answers the facts give: a checked URL, „no website”, or only „has one” while the address is missing."""
    url = get_website_url(facts.website_url)
    if url:
        return {"has_website": True, "website_url": url}
    if facts.has_website is False:
        return {"has_website": False, "website_url": None}
    return {"has_website": True} if facts.has_website else {}


def get_website_url(text: str | None) -> str | None:
    """Returns a website address the owner typed as a full URL, or `None` when it isn't one or is a social or Google page."""
    value = (text or "").strip()
    if not value or " " in value:
        return None
    domain = get_domain(value)
    if "." not in domain or any(is_on_host(domain, host) for host in NOT_WEBSITE_HOSTS):
        return None
    return value if "://" in value else f"https://{value}"


async def get_google_update(
    answers: OnboardingAnswers, facts: OnboardingFacts, shown_places: list[PlaceCandidate] | None
) -> tuple[dict[str, Any], LinkProblem | None]:
    """Returns the Google Maps answers the facts give: a place from a pasted link or a named card, no profile or later."""
    link = (facts.maps_url or "").strip()
    if link and link != answers.maps_url:
        try:
            place = await resolve_link(link)
        except ApiError as error:
            logger.info("Maps link gave no place during onboarding: %s", error.code)
            return {}, "unreadable" if error.code == "unreadable_link" else "unavailable"
        return {"google_choice": "place", "place": place, "maps_url": link}, None
    if facts.picked_place and shown_places and 1 <= facts.picked_place <= len(shown_places):
        return {"google_choice": "place", "place": shown_places[facts.picked_place - 1], "maps_url": None}, None
    if facts.google_choice:
        return {"google_choice": facts.google_choice, "place": None, "maps_url": None}, None
    return {}, None


def get_social_update(facts: OnboardingFacts) -> dict[str, Any]:
    """Returns the Instagram and TikTok answers the facts give, as profile links."""
    handle = get_instagram_handle(get_account_text(facts.instagram))
    instagram = f"https://www.instagram.com/{handle}" if handle else None
    tiktok = get_tiktok_url(get_account_text(facts.tiktok))
    if instagram or tiktok:
        update: dict[str, Any] = {"has_social": True}
        if instagram:
            update["instagram_url"] = instagram
        if tiktok:
            update["tiktok_url"] = tiktok
        return update
    if facts.has_social is False:
        return {"has_social": False, "instagram_url": None, "tiktok_url": None}
    return {"has_social": True} if facts.has_social else {}


def get_account_text(text: str | None) -> str | None:
    """Returns what the owner typed for an account when it can be one: a link, an @name, or a bare name that isn't a plain answer."""
    value = (text or "").strip()
    if "/" in value or value.startswith("@"):
        return value
    return value if len(value) >= 3 and value.lower() not in NOT_ACCOUNT_NAMES else None


def get_tiktok_url(text: str | None) -> str | None:
    """Returns the TikTok profile link for a link or a typed „@name”, or `None` when it is neither."""
    value = (text or "").strip()
    match = re.search(r"tiktok\.com/@([A-Za-z0-9_.]+)", value) or re.fullmatch(r"@?([A-Za-z0-9_.]+)", value)
    return f"https://www.tiktok.com/@{match.group(1)}" if match else None


def get_missing_fields(answers: OnboardingAnswers) -> list[OnboardingField]:
    """Returns what the onboarding still needs, in the order the assistant asks for it."""
    report = answers.self_report
    has_google = answers.google_choice != "none"
    has_social = answers.has_social is not False
    checks: list[tuple[OnboardingField, bool]] = [
        ("business_name", not answers.business_name),
        ("business_type", not answers.business_type or not answers.business_type_label_ro),
        ("city", not answers.city),
        ("neighborhood", not answers.neighborhood),
        ("website", answers.has_website is None or bool(answers.has_website and not answers.website_url)),
        ("google_profile", answers.google_choice is None),
        ("profile_claimed", has_google and report.profile_claimed is None),
        ("has_google_description", has_google and report.has_google_description is None),
        ("last_google_post", has_google and report.last_google_post is None),
        ("social", answers.has_social is None or bool(answers.has_social and not (answers.instagram_url or answers.tiktok_url))),
        ("last_social_post", has_social and report.last_social_post is None),
        ("platforms", answers.platforms is None),
    ]
    return [field for field, is_missing in checks if is_missing]


def get_reply_text(
    reply: OnboardingReply,
    asks: OnboardingField | None,
    places: list[PlaceCandidate] | None,
    shown_places: list[PlaceCandidate] | None,
    link_problem: LinkProblem | None,
) -> str:
    """Returns the message to show, explaining first a pasted Maps link that gave no place."""
    if link_problem and asks == "google_profile":
        return LINK_PROBLEMS_RO[link_problem]
    text = get_question_text(reply, asks, places, shown_places)
    return f"{LINK_LATER_RO} {text}" if link_problem else text


def get_question_text(
    reply: OnboardingReply,
    asks: OnboardingField | None,
    places: list[PlaceCandidate] | None,
    shown_places: list[PlaceCandidate] | None,
) -> str:
    """Returns Gemini's message, or the fixed question when Gemini asks for something else than what is missing first or
    didn't know the places on the cards."""
    is_reply_usable = reply.asks == asks and reply.reply_ro.strip() != ""
    if is_reply_usable and (asks != "google_profile" or places == shown_places):
        return reply.reply_ro.strip()
    if asks is None:
        return DONE_RO
    if asks == "google_profile":
        return get_places_question(places)
    return QUESTIONS_RO[asks]


def get_places_question(places: list[PlaceCandidate] | None) -> str:
    """Returns the Google Maps question for the places on the cards."""
    if places is None:
        return QUESTIONS_RO["google_profile"]
    if not places:
        return NO_PLACES_RO
    if len(places) == 1:
        return "Am găsit 1 loc pe Google Maps care se potrivește. Ești tu?"
    return f"Am găsit {len(places)} locuri pe Google Maps care se potrivesc. Care dintre ele ești tu?"
