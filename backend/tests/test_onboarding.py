"""Checks the onboarding's answer rules and how a turn picks its message, with fake Gemini and Places calls."""

import asyncio

import pytest

from app.errors import ApiError
from app.models import ErrorCode, OnboardingAnswers, OnboardingMessage, PlaceCandidate, SelfReport
from app.services import onboarding
from app.services.onboarding import OnboardingFacts, OnboardingReply, get_missing_fields, get_updated_answers

EMPTY_ANSWERS = OnboardingAnswers(
    business_name=None,
    business_type=None,
    business_type_label_ro=None,
    city=None,
    neighborhood=None,
    has_website=None,
    website_url=None,
    google_choice=None,
    place=None,
    maps_url=None,
    self_report=SelfReport(profile_claimed=None, has_google_description=None, last_google_post=None, last_social_post=None),
    has_social=None,
    instagram_url=None,
    tiktok_url=None,
    platforms=None,
)
"""The answers before the owner has said anything."""

NO_FACTS = OnboardingFacts.model_validate({field: None for field in OnboardingFacts.model_fields})
"""A message that states nothing."""

ORIGO = PlaceCandidate(
    place_id="origo", name="Origo", address="Strada Lipscani 9", type_label_ro="Cafenea", rating=4.7, review_count=5098, best=True
)
"""A place the fake search finds."""

LOCATED = EMPTY_ANSWERS.model_copy(
    update={
        "business_name": "Origo",
        "business_type": "cafenea",
        "business_type_label_ro": "Cafenea",
        "city": "București",
        "neighborhood": "Centrul Vechi",
    }
)
"""The answers once the name, the type and the location are in."""


def get_facts(**facts: object) -> OnboardingFacts:
    """Returns facts with only the given ones set."""
    return NO_FACTS.model_copy(update=facts)


def run_turn(
    monkeypatch: pytest.MonkeyPatch,
    answers: OnboardingAnswers,
    reply: OnboardingReply,
    places: list[PlaceCandidate],
    link_error: ErrorCode = "unreadable_link",
) -> onboarding.OnboardingTurn:
    """Runs one turn with Gemini answering `reply`, the place search finding `places` and every Maps link failing."""

    async def fake_json_call(*_args: object, **_kwargs: object) -> OnboardingReply:
        return reply

    async def fake_search(*_args: object) -> list[PlaceCandidate]:
        return places

    async def fake_resolve(_url: str) -> PlaceCandidate:
        raise ApiError(link_error)

    monkeypatch.setattr(onboarding, "json_call", fake_json_call)
    monkeypatch.setattr(onboarding, "search_places", fake_search)
    monkeypatch.setattr(onboarding, "resolve_link", fake_resolve)
    messages = [OnboardingMessage(role="user", text="…")]
    return asyncio.run(onboarding.get_onboarding_turn(messages, answers))


def test_missing_fields_skip_questions_that_no_longer_apply() -> None:
    """Checks the order of the questions and that „no Google profile” and „no social” skip their follow-ups."""
    assert get_missing_fields(EMPTY_ANSWERS)[:6] == [
        "business_name",
        "business_type",
        "city",
        "neighborhood",
        "website",
        "google_profile",
    ]
    no_google = get_missing_fields(LOCATED.model_copy(update={"google_choice": "none", "has_social": False}))
    assert no_google == ["website", "platforms"]
    has_website = LOCATED.model_copy(update={"has_website": True})
    assert get_missing_fields(has_website)[0] == "website"


def test_facts_are_checked_before_they_are_kept() -> None:
    """Checks websites, social links, type labels and „no website” as Gemini may return them."""
    facts = get_facts(
        business_type="cafenea",
        website_url="origocoffee.ro",
        instagram="@origo_coffee",
        tiktok="tiktok.com/@origo.coffee?lang=ro",
    )
    answers, _ = asyncio.run(get_updated_answers(EMPTY_ANSWERS, facts, None))
    assert answers.business_type_label_ro == "Cafenea"
    lowercase, _ = asyncio.run(
        get_updated_answers(EMPTY_ANSWERS, get_facts(business_type="cafenea", business_type_label_ro="cafenea de specialitate"), None)
    )
    assert lowercase.business_type_label_ro == "Cafenea de specialitate"
    assert answers.website_url == "https://origocoffee.ro"
    assert answers.instagram_url == "https://www.instagram.com/origo_coffee"
    assert answers.tiktok_url == "https://www.tiktok.com/@origo.coffee"
    assert answers.has_social is True
    facebook, _ = asyncio.run(get_updated_answers(EMPTY_ANSWERS, get_facts(website_url="facebook.com/origo"), None))
    assert facebook.website_url is None
    other, _ = asyncio.run(get_updated_answers(EMPTY_ANSWERS, get_facts(business_type="altceva"), None))
    assert "business_type" in get_missing_fields(other)
    no_site, _ = asyncio.run(get_updated_answers(answers, get_facts(has_website=False), None))
    assert (no_site.has_website, no_site.website_url) == (False, None)
    maps_page, _ = asyncio.run(get_updated_answers(EMPTY_ANSWERS, get_facts(website_url="https://maps.google.ro/?cid=1"), None))
    assert maps_page.website_url is None
    refusals, _ = asyncio.run(get_updated_answers(EMPTY_ANSWERS, get_facts(instagram="da", tiktok="nu"), None))
    assert (refusals.instagram_url, refusals.tiktok_url, refusals.has_social) == (None, None, None)


def test_no_google_profile_drops_the_google_answers() -> None:
    """Checks that switching to „no Google profile” or „no social” clears the self-reported answers that no longer apply."""
    report = SelfReport(
        profile_claimed="da", has_google_description="nu", last_google_post="mai_demult", last_social_post="luna_asta"
    )
    answers = LOCATED.model_copy(update={"google_choice": "place", "place": ORIGO, "has_social": True, "self_report": report})
    changed, _ = asyncio.run(get_updated_answers(answers, get_facts(google_choice="none", has_social=False), None))
    assert changed.place is None
    assert changed.self_report == SelfReport(
        profile_claimed=None, has_google_description=None, last_google_post=None, last_social_post=None
    )


def test_a_card_named_in_words_is_picked() -> None:
    """Checks that „primul” picks the first card, and a number past the cards picks nothing."""
    picked, _ = asyncio.run(get_updated_answers(LOCATED, get_facts(picked_place=1), [ORIGO]))
    assert (picked.google_choice, picked.place) == ("place", ORIGO)
    missed, _ = asyncio.run(get_updated_answers(LOCATED, get_facts(picked_place=2), [ORIGO]))
    assert missed.google_choice is None


def test_reply_asking_out_of_order_is_replaced_by_the_fixed_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that a reply asking for anything but the first missing answer gives way to that answer's question."""
    reply = OnboardingReply(facts=get_facts(business_name="Origo"), asks="website", reply_ro="Ai site?")
    turn = run_turn(monkeypatch, EMPTY_ANSWERS, reply, [])
    assert turn.missing[0] == "business_type"
    assert turn.reply_ro == onboarding.QUESTIONS_RO["business_type"]
    good = OnboardingReply(facts=get_facts(business_name="Origo"), asks="business_type", reply_ro="Ce fel de afacere e Origo?")
    assert run_turn(monkeypatch, EMPTY_ANSWERS, good, []).reply_ro == "Ce fel de afacere e Origo?"


def test_places_found_in_the_same_turn_get_the_cards_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that the place cards come with a question that counts them when Gemini hadn't seen them."""
    reply = OnboardingReply(
        facts=get_facts(
            business_name="Origo", business_type="cafenea", city="București", neighborhood="Centrul Vechi", has_website=False
        ),
        asks="google_profile",
        reply_ro="Te caut pe Google.",
    )
    turn = run_turn(monkeypatch, EMPTY_ANSWERS, reply, [ORIGO])
    assert turn.candidates == [ORIGO]
    assert turn.reply_ro == "Am găsit 1 loc pe Google Maps care se potrivește. Ești tu?"
    seen = run_turn(monkeypatch, LOCATED.model_copy(update={"has_website": False}), reply, [ORIGO])
    assert seen.reply_ro == "Te caut pe Google."


def test_unreadable_link_keeps_the_google_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that a pasted link that can't be read is explained and the place cards stay."""
    reply = OnboardingReply(
        facts=get_facts(maps_url="https://maps.app.goo.gl/x"), asks="profile_claimed", reply_ro="Ai revendicat?"
    )
    turn = run_turn(monkeypatch, LOCATED.model_copy(update={"has_website": False}), reply, [ORIGO])
    assert turn.missing[0] == "google_profile"
    assert turn.reply_ro == onboarding.LINK_PROBLEMS_RO["unreadable"]
    assert turn.candidates == [ORIGO]


def test_link_failing_early_keeps_the_other_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that a link pasted before its question, while Google Maps is down, keeps the message's other facts and says so."""
    reply = OnboardingReply(
        facts=get_facts(business_name="Origo", maps_url="https://maps.app.goo.gl/x"), asks="business_type", reply_ro="Ce fel?"
    )
    turn = run_turn(monkeypatch, EMPTY_ANSWERS, reply, [], link_error="upstream_error")
    assert turn.answers.business_name == "Origo"
    assert turn.reply_ro == f"{onboarding.LINK_LATER_RO} Ce fel?"


def test_everything_answered_ends_the_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    """Checks that the last answer leaves nothing missing and the fixed closing line replaces a reply that still asks."""
    answers = LOCATED.model_copy(
        update={
            "has_website": False,
            "google_choice": "none",
            "has_social": False,
        }
    )
    reply = OnboardingReply(facts=get_facts(platforms=["glovo", "glovo"]), asks="platforms", reply_ro="Și altele?")
    turn = run_turn(monkeypatch, answers, reply, [])
    assert turn.missing == []
    assert turn.answers.platforms == ["glovo"]
    assert turn.reply_ro == onboarding.DONE_RO
