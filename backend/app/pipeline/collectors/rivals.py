"""3.9b Rivals: Google details for the businesses Gemini recommends instead, and the comparison against them."""

import asyncio
import logging
import statistics

from app.models import ChapterId, CompareRow, Comparison, ComparisonAction
from app.pipeline.assemble import get_compare_row
from app.pipeline.canonical import get_canonical
from app.pipeline.collectors.live_test import NamedPlace
from app.pipeline.romanian import get_list_phrase
from app.pipeline.types import CheckResult

logger = logging.getLogger(__name__)

RIVAL_DETAILS_TIMEOUT_SECONDS = 10
"""How long one rival's Place Details may take."""

SAME_RATING_MARGIN = 0.05
"""How far below the rivals' median a rating still counts as „la fel de bună”."""

BETTER_RATING_MARGIN = 0.15
"""How far above the rivals' median a rating counts as better."""

GAP_ACTIONS: dict[str, tuple[str, str, ChapterId]] = {
    "recenziile": ("Strânge mai multe recenzii", "R01", "recenzii"),
    "fotografiile": ("Adaugă fotografii", "G05", "profil"),
    "programul complet": ("Completează programul", "G03", "profil"),
}
"""For each gap, the button that opens the problem fixing it: label, check and chapter."""


async def get_rival_rows(rivals: list[NamedPlace]) -> list[CompareRow]:
    """Returns the comparison rows of the rivals with a Google place ID; a rival whose details fail keeps only its name."""
    rows = await asyncio.gather(*(get_rival_row(rival) for rival in rivals if rival.place_id))
    return list(rows)


async def get_rival_row(rival: NamedPlace) -> CompareRow:
    """Returns one rival's comparison row from its Place Details, or only its name when they fail or take too long."""
    try:
        return get_compare_row(await asyncio.wait_for(get_canonical(rival.place_id or ""), RIVAL_DETAILS_TIMEOUT_SECONDS))
    except Exception:
        logger.exception("Rival details failed for %s", rival.name)
        return CompareRow(
            name=rival.name,
            place_id=rival.place_id,
            review_count=None,
            rating=None,
            photo_count=None,
            photo_count_capped=False,
            hours_complete=None,
        )


def get_comparison(me: CompareRow, rivals: list[CompareRow], checks: list[CheckResult]) -> Comparison:
    """Returns the comparison: the rating against the rivals, what the business lacks, and buttons for the open problems."""
    if not rivals:
        return Comparison(me=me, rivals=[], insights_ro=[], actions=[])
    insights = [insight for insight in [get_rating_insight(me, rivals)] if insight]
    gaps = get_gaps(me, rivals)
    if gaps:
        insights.append(f"Îți lipsesc {get_list_phrase(gaps)}, iar LLM-ul se uită exact la acestea.")
    open_checks = {check.check_id for check in checks if check.status in ("fail", "partial") and not check.claimed_fixed}
    actions = []
    for gap in gaps:
        label, check_id, chapter_id = GAP_ACTIONS[gap]
        if check_id in open_checks:
            actions.append(ComparisonAction(label_ro=label, check_id=check_id, chapter_id=chapter_id))
    return Comparison(me=me, rivals=rivals, insights_ro=insights, actions=actions)


def get_rating_insight(me: CompareRow, rivals: list[CompareRow]) -> str | None:
    """Returns how the rating compares with the rivals' median, or `None` when a rating is missing."""
    ratings = [rival.rating for rival in rivals if rival.rating is not None]
    if me.rating is None or not ratings:
        return None
    difference = me.rating - statistics.median(ratings)
    if difference >= BETTER_RATING_MARGIN:
        return "Ai o notă mai bună decât ei."
    if difference >= -SAME_RATING_MARGIN:
        return "Ai o notă la fel de bună ca ei."
    return "Ei au o notă mai mare decât tine."


def get_gaps(me: CompareRow, rivals: list[CompareRow]) -> list[str]:
    """Returns what the rivals have and the business lacks: far fewer reviews, fewer photos, incomplete hours."""
    gaps = []
    review_counts = [rival.review_count for rival in rivals if rival.review_count is not None]
    if review_counts and (me.review_count or 0) < statistics.median(review_counts) / 2:
        gaps.append("recenziile")
    photo_counts = [rival.photo_count for rival in rivals if rival.photo_count is not None]
    if photo_counts and (me.photo_count or 0) < min(statistics.median(photo_counts), 10):
        gaps.append("fotografiile")
    rivals_complete = sum(1 for rival in rivals if rival.hours_complete)
    if me.hours_complete is False and rivals_complete * 2 > len(rivals):
        gaps.append("programul complet")
    return gaps
