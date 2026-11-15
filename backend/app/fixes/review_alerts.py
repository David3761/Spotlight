"""WhatsApp review alerts: when a new Google review arrives, the owner gets a suggested reply on WhatsApp.

A watcher checks every subscribed business's newest reviews on SerpApi every twelve hours (about 60 of the free
plan's 250 monthly searches per business). Reviews already there when alerts were turned on never trigger a message;
a review whose alert didn't go through is tried again at the next check.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlmodel import Field, SQLModel, select

from app.db import get_session
from app.errors import ApiError
from app.fixes import whatsapp
from app.fixes.generate import get_facts_text, get_prompt
from app.fixes.schemas import ReviewAlerts, ReviewAlertSent, ReviewReplyDraft
from app.jobs import is_demo_scan
from app.llm.client import json_call
from app.pipeline.collectors.reviews import get_recent_reviews, get_recent_reviews_search
from app.pipeline.normalize import format_national_phone, normalize_phone
from app.pipeline.serpapi import SerpApiError, send_search
from app.services.resolution import load_facts, load_inputs, load_report

logger = logging.getLogger(__name__)

CHECK_INTERVAL = timedelta(hours=12)
"""How often each subscribed business's reviews are checked."""

WATCH_TICK_SECONDS = 600
"""How often the watcher wakes to look for businesses whose check is due, so a restart never spends an early check."""

MAX_ALERTS_PER_CHECK = 3
"""The most messages one check sends; more new reviews than this get only the newest ones."""

REVIEW_TEXT_LIMIT = 600
"""How much of a review's text the WhatsApp message quotes."""

DELIVERY_FAILED_RO = (
    "Nu am putut trimite mesajul pe WhatsApp. Dacă au trecut peste 24 de ore de la ultimul tău mesaj către noi, "
    "trimite din nou «Start»."
)
"""The error shown when WhatsApp refuses a message, true whatever the cause."""


class ReviewAlertRow(SQLModel, table=True):
    """A business owner's WhatsApp review alerts for one scan, with the reviews already seen."""

    __tablename__ = "review_alerts"

    scan_id: str = Field(primary_key=True)
    place_id: str
    phone: str
    seen_review_ids: str = "[]"
    delivery_failed: bool = False
    checked_at: datetime


def get_review_alerts(scan_id: str) -> ReviewAlerts:
    """Returns the scan's review alerts: on or off, the phone, the link that opens the 24-hour window, the last delivery."""
    can_simulate = is_demo_scan(load_inputs(scan_id))
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
    return ReviewAlerts(
        enabled=row is not None,
        phone=format_national_phone(row.phone) if row else None,
        whatsapp_link=whatsapp.get_start_link(),
        delivery_problem_ro=DELIVERY_FAILED_RO if row and row.delivery_failed else None,
        can_simulate=can_simulate,
    )


async def enable_review_alerts(scan_id: str, phone: str) -> ReviewAlerts:
    """Turns on alerts for a phone number, marking the current reviews as seen so only later ones send a message.

    Raises `ApiError` when the number isn't valid, the business has no Google profile, WhatsApp isn't set up or the
    current reviews can't be read (without them, every recent review would look new).
    """
    phone_e164 = normalize_phone(phone)
    if phone_e164 is None:
        raise ApiError("invalid_phone")
    place_id = load_report(scan_id).business.place_id
    if place_id is None:
        raise ApiError("place_not_found", "Fără Profil Google nu avem recenzii de urmărit.")
    if not whatsapp.is_configured():
        raise ApiError("upstream_error", "Nu putem trimite mesaje pe WhatsApp acum.")
    try:
        reviews = await get_newest_reviews(place_id)
    except (SerpApiError, httpx.HTTPError, ValueError) as error:
        raise ApiError("upstream_error", "Nu am putut citi recenziile acum. Încearcă din nou.") from error
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id) or ReviewAlertRow(
            scan_id=scan_id, place_id=place_id, phone=phone_e164, checked_at=datetime.now(UTC)
        )
        row.phone = phone_e164
        row.seen_review_ids = json.dumps(sorted(set(json.loads(row.seen_review_ids)) | get_review_ids(reviews)))
        row.delivery_failed = False
        session.add(row)
        session.commit()
    return get_review_alerts(scan_id)


def disable_review_alerts(scan_id: str) -> ReviewAlerts:
    """Turns off the scan's review alerts."""
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
        if row is not None:
            session.delete(row)
            session.commit()
    return get_review_alerts(scan_id)


async def simulate_review_alert(scan_id: str) -> ReviewAlertSent:
    """Sends the alert for the newest review right away, as if it had just arrived: the demo's „Simulează o recenzie nouă”."""
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
    if row is None:
        raise ApiError("alerts_off")
    try:
        reviews = await get_recent_reviews(row.place_id)
    except SerpApiError as error:
        raise ApiError("upstream_error", "Nu am putut citi recenziile acum. Încearcă din nou.") from error
    if not reviews:
        raise ApiError("no_reviews")
    review = next((review for review in reviews if get_review_text(review)), reviews[0])
    reply = await get_reply_suggestion(scan_id, review)
    if not await send_review_alert(row.scan_id, row.phone, review, reply):
        raise ApiError("upstream_error", DELIVERY_FAILED_RO)
    return ReviewAlertSent(author=get_author(review), rating=get_rating(review), reply_ro=reply)


async def watch_reviews() -> None:
    """Checks the subscribed businesses for new reviews whenever their check is due, for as long as the app runs."""
    while True:
        try:
            await check_due_alerts()
        except Exception:
            logger.exception("Review watcher round failed")
        await asyncio.sleep(WATCH_TICK_SECONDS)


async def check_due_alerts() -> None:
    """Checks every subscription whose last check is older than the interval; nothing runs while WhatsApp isn't set up."""
    if not whatsapp.is_configured():
        return
    due_before = datetime.now(UTC) - CHECK_INTERVAL
    with get_session() as session:
        scan_ids = [row.scan_id for row in session.exec(select(ReviewAlertRow)).all() if get_aware(row.checked_at) <= due_before]
    for scan_id in scan_ids:
        try:
            await check_new_reviews(scan_id)
        except Exception:
            logger.exception("Checking new reviews failed for scan %s", scan_id)


async def check_new_reviews(scan_id: str) -> None:
    """Sends an alert for each new unanswered review (the newest few), then marks every review read as seen.

    The check time is saved before SerpApi is asked, so a failing search waits a full interval instead of spending
    the monthly quota every few minutes.
    """
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
        if row is None:
            return
        row.checked_at = datetime.now(UTC)
        session.add(row)
        session.commit()
        session.refresh(row)
    reviews = await get_newest_reviews(row.place_id)
    seen = set(json.loads(row.seen_review_ids))
    new_reviews = [
        review for review in reviews if review.get("review_id") and review["review_id"] not in seen and not review.get("response")
    ]
    undelivered: set[str] = set()
    for review in reversed(new_reviews[:MAX_ALERTS_PER_CHECK]):
        try:
            delivered = await send_review_alert(scan_id, row.phone, review, await get_reply_suggestion(scan_id, review))
        except Exception:
            logger.exception("Writing the alert failed for scan %s", scan_id)
            delivered = False
        if delivered:
            mark_seen(scan_id, {review["review_id"]})
        else:
            undelivered.add(review["review_id"])
    mark_seen(scan_id, get_review_ids(reviews) - undelivered)


def mark_seen(scan_id: str, review_ids: set[str]) -> None:
    """Adds reviews to the subscription's seen list, so they never send an alert again."""
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
        if row is None:
            return
        row.seen_review_ids = json.dumps(sorted(set(json.loads(row.seen_review_ids)) | review_ids))
        session.add(row)
        session.commit()


async def get_newest_reviews(place_id: str) -> list[dict[str, Any]]:
    """Returns a place's newest reviews straight from SerpApi, never from the day's cache, so a new review shows up."""
    data = (await send_search(get_recent_reviews_search(place_id))).json()
    if data.get("error"):
        raise SerpApiError(str(data["error"]))
    return data.get("reviews", [])


async def get_reply_suggestion(scan_id: str, review: dict[str, Any]) -> str:
    """Returns a public reply to a review, written from the business's facts in the review's language."""
    facts = load_facts(scan_id)
    rating = get_rating(review)
    prompt = get_prompt("fix_review_reply").format(
        facts=get_facts_text(facts, facts.type_label_ro),
        author=get_author(review),
        rating=f"{rating:g}" if rating is not None else "necunoscut",
        review_text=get_review_text(review) or "(fără text, doar stele)",
    )
    draft = await json_call(prompt, ReviewReplyDraft, tier="smart")
    return draft.reply.strip()


async def send_review_alert(scan_id: str, phone_e164: str, review: dict[str, Any], reply: str) -> bool:
    """Sends the WhatsApp alert for one review and records whether it was delivered; returns `True` when it was."""
    business = load_report(scan_id).business
    rating = get_rating(review)
    stars = f": {rating:g} din 5 stele" if rating is not None else ""
    lines = [f"Recenzie nouă pe Google pentru {business.name}{stars}, de la {get_author(review)}."]
    text = get_review_text(review)
    if text:
        quoted = text if len(text) <= REVIEW_TEXT_LIMIT else f"{text[:REVIEW_TEXT_LIMIT].rstrip()}…"
        lines.append(f"„{quoted}”")
    lines += ["", "Răspuns sugerat, gata de copiat:", reply]
    link = review.get("link") or business.google_maps_uri
    if link:
        lines += ["", f"Răspunde aici: {link}"]
    try:
        await whatsapp.send_text(phone_e164, "\n".join(lines))
        delivered = True
    except whatsapp.WhatsAppError:
        logger.exception("WhatsApp alert failed for scan %s", scan_id)
        delivered = False
    with get_session() as session:
        row = session.get(ReviewAlertRow, scan_id)
        if row is not None:
            row.delivery_failed = not delivered
            session.add(row)
            session.commit()
    return delivered


def get_review_ids(reviews: list[dict[str, Any]]) -> set[str]:
    """Returns the IDs of the reviews that have one."""
    return {review["review_id"] for review in reviews if review.get("review_id")}


def get_review_text(review: dict[str, Any]) -> str:
    """Returns a review's text as its author wrote it, or an empty string for a rating without text."""
    extracted = review.get("extracted_snippet")
    original = extracted.get("original") if isinstance(extracted, dict) else None
    return (original or review.get("snippet") or "").strip()


def get_author(review: dict[str, Any]) -> str:
    """Returns the name of a review's author."""
    user = review.get("user")
    name = user.get("name") if isinstance(user, dict) else None
    return name or "un client"


def get_rating(review: dict[str, Any]) -> float | None:
    """Returns a review's star rating."""
    rating = review.get("rating")
    return float(rating) if isinstance(rating, int | float) else None


def get_aware(moment: datetime) -> datetime:
    """Returns a stored time as UTC-aware; SQLite gives back stored times without their time zone."""
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)
