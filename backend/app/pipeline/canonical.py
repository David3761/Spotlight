"""The canonical profile: the business as Google's Place Details describe it, the source of truth for every comparison."""

from typing import Any

from pydantic import BaseModel

from app.pipeline.normalize import MINUTES_PER_DAY, WeeklyHours, normalize_phone
from app.pipeline.places_api import places_request
from app.pipeline.romanian import get_date_ro

DETAILS_FIELD_MASK = "id,displayName,primaryType,primaryTypeDisplayName,types,businessStatus,googleMapsUri,formattedAddress,shortFormattedAddress,addressComponents,location,nationalPhoneNumber,internationalPhoneNumber,websiteUri,regularOpeningHours,currentOpeningHours,rating,userRatingCount,reviews,photos,editorialSummary,priceLevel,priceRange,dineIn,takeout,delivery,outdoorSeating,servesCoffee,servesBreakfast,allowsDogs,goodForGroups,paymentOptions,accessibilityOptions"
"""The Place Details fields the pipeline reads (§3 step 2)."""

ATTRIBUTE_FIELDS = [
    "dineIn",
    "takeout",
    "delivery",
    "outdoorSeating",
    "servesCoffee",
    "servesBreakfast",
    "allowsDogs",
    "goodForGroups",
]
"""The yes/no attributes Place Details returns at the top level."""

ATTRIBUTE_GROUPS = ["paymentOptions", "accessibilityOptions"]
"""The attribute groups whose yes/no fields are flattened into `attributes`."""


ATTRIBUTE_LABELS_RO = {
    "dineIn": "servire la masă",
    "takeout": "la pachet",
    "delivery": "livrare",
    "outdoorSeating": "terasă",
    "servesCoffee": "cafea",
    "servesBreakfast": "mic dejun",
    "allowsDogs": "câini acceptați",
    "goodForGroups": "potrivit pentru grupuri",
    "acceptsCreditCards": "plata cu cardul",
    "acceptsNfc": "plata cu telefonul",
    "wheelchairAccessibleEntrance": "intrare accesibilă cu scaunul cu rotile",
}
"""Romanian labels of the Google attributes the app talks about."""


class PlaceReview(BaseModel):
    """One of the reviews Place Details returns (at most five, by relevance)."""

    publish_time: str | None
    rating: int | None
    text: str | None


class CanonicalProfile(BaseModel):
    """A business's Google profile, normalized."""

    place_id: str
    name: str
    primary_type: str | None
    primary_type_label: str | None
    types: list[str]
    business_status: str | None
    google_maps_uri: str | None
    formatted_address: str | None
    short_address: str | None
    lat: float | None
    lng: float | None
    national_phone: str | None
    phone_e164: str | None
    website: str | None
    has_regular_hours: bool
    weekly_hours: WeeklyHours
    hours_ro: list[str]
    special_days: list[str]
    rating: float | None
    review_count: int | None
    photo_count: int
    reviews: list[PlaceReview]
    price_level: str | None
    price_range: str | None
    attributes: dict[str, bool]

    @property
    def attributes_ro(self) -> list[str]:
        """The attributes that are true, as capitalized Romanian labels („Terasă”, „Plata cu cardul”)."""
        return [label[:1].upper() + label[1:] for key, label in ATTRIBUTE_LABELS_RO.items() if self.attributes.get(key)]

    @property
    def special_days_ro(self) -> list[str]:
        """The upcoming special days as Romanian dates („25 decembrie 2026”)."""
        return [get_date_ro(day) for day in self.special_days]

    @property
    def hours_complete(self) -> bool:
        """Whether the profile has hours for the whole week; holiday hours aren't visible ahead, so they don't count."""
        return self.has_regular_hours


async def get_canonical(place_id: str) -> CanonicalProfile:
    """Returns the canonical profile of a Google place."""
    return parse_canonical(await places_request("GET", f"places/{place_id}", DETAILS_FIELD_MASK))


def parse_canonical(data: dict[str, Any]) -> CanonicalProfile:
    """Returns the canonical profile read from a Place Details response."""
    regular_hours = data.get("regularOpeningHours") or {}
    current_hours = data.get("currentOpeningHours") or {}
    location = data.get("location") or {}
    national_phone = data.get("nationalPhoneNumber")
    return CanonicalProfile(
        place_id=data["id"],
        name=(data.get("displayName") or {}).get("text", ""),
        primary_type=data.get("primaryType"),
        primary_type_label=(data.get("primaryTypeDisplayName") or {}).get("text"),
        types=data.get("types", []),
        business_status=data.get("businessStatus"),
        google_maps_uri=data.get("googleMapsUri"),
        formatted_address=data.get("formattedAddress"),
        short_address=data.get("shortFormattedAddress"),
        lat=location.get("latitude"),
        lng=location.get("longitude"),
        national_phone=national_phone,
        phone_e164=normalize_phone(data.get("internationalPhoneNumber") or national_phone or ""),
        website=data.get("websiteUri"),
        has_regular_hours=bool(regular_hours),
        weekly_hours=get_weekly_hours(regular_hours.get("periods", [])) if regular_hours else {},
        hours_ro=[line[:1].upper() + line[1:] for line in regular_hours.get("weekdayDescriptions", [])],
        special_days=[get_iso_date(day["date"]) for day in current_hours.get("specialDays", []) if "date" in day],
        rating=data.get("rating"),
        review_count=data.get("userRatingCount"),
        photo_count=len(data.get("photos", [])),
        reviews=[
            PlaceReview(
                publish_time=review.get("publishTime"),
                rating=review.get("rating"),
                text=(review.get("text") or {}).get("text"),
            )
            for review in data.get("reviews", [])
        ],
        price_level=data.get("priceLevel"),
        price_range=get_price_range(data.get("priceRange")),
        attributes=get_attributes(data),
    )


def get_weekly_hours(periods: list[dict[str, Any]]) -> WeeklyHours:
    """Returns opening intervals per day (0 = Monday) from Google's periods (0 = Sunday); closed days get `[]`.

    A period without a close time means open around the clock; one that closes on a later day ends after midnight.
    """
    hours: WeeklyHours = {day: [] for day in range(7)}
    for period in periods:
        opening = period["open"]
        closing = period.get("close")
        start = opening.get("hour", 0) * 60 + opening.get("minute", 0)
        if closing is None:
            return {day: [(0, MINUTES_PER_DAY)] for day in range(7)}
        days_later = (closing["day"] - opening["day"]) % 7
        end = closing.get("hour", 0) * 60 + closing.get("minute", 0) + days_later * MINUTES_PER_DAY
        hours[(opening["day"] + 6) % 7].append((start, end))
    return hours


def get_iso_date(date: dict[str, int]) -> str:
    """Returns a Google date object as `YYYY-MM-DD`."""
    return f"{date['year']:04d}-{date['month']:02d}-{date['day']:02d}"


def get_price_range(price_range: dict[str, Any] | None) -> str | None:
    """Returns a price range as text, e.g. „20–40 RON”."""
    if not price_range:
        return None
    start = price_range.get("startPrice") or {}
    end = price_range.get("endPrice") or {}
    currency = start.get("currencyCode") or end.get("currencyCode") or ""
    amounts = [money.get("units", "0") for money in (start, end) if money]
    if not amounts:
        return None
    return f"{'–'.join(amounts)} {currency}".strip()


def get_attributes(data: dict[str, Any]) -> dict[str, bool]:
    """Returns every yes/no attribute the profile states, groups flattened (e.g. `acceptsCreditCards`)."""
    attributes = {field: data[field] for field in ATTRIBUTE_FIELDS if isinstance(data.get(field), bool)}
    for group in ATTRIBUTE_GROUPS:
        attributes.update({key: value for key, value in (data.get(group) or {}).items() if isinstance(value, bool)})
    return attributes
