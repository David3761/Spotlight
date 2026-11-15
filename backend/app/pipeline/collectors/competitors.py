"""3.9a Nearby competitors: the most popular businesses of the same type within 1.5 km, the benchmark for R01."""

from pydantic import BaseModel

from app.models import BusinessType
from app.pipeline.canonical import CanonicalProfile
from app.pipeline.places_api import places_request

NEARBY_RADIUS_METERS = 1500.0
"""How far around the business competitors are looked for."""

NEARBY_COUNT = 3
"""How many competitors the review benchmark uses."""

NEARBY_FIELD_MASK = "places.id,places.displayName,places.userRatingCount,places.rating"
"""The Nearby Search fields the benchmark needs; review counts come with the search, no Place Details needed."""

TYPE_PLACE_TYPES: dict[BusinessType, list[str]] = {
    "cafenea": ["coffee_shop", "cafe"],
    "restaurant": ["restaurant"],
    "bar": ["bar", "pub", "wine_bar"],
    "salon": ["beauty_salon", "hair_salon", "nail_salon", "barber_shop"],
    "hotel": ["hotel"],
    "magazin": ["store"],
}
"""The Google place types searched for each business type; „altceva” uses the profile's own main type."""

GENERIC_PLACE_TYPES = {"service", "store", "establishment", "point_of_interest", "food"}
"""Google's catch-all main types, too broad to find comparable businesses nearby (a hospital for a bike repair shop)."""


class NearbyCompetitor(BaseModel):
    """A popular business of the same type nearby."""

    place_id: str
    name: str
    review_count: int | None
    rating: float | None


async def get_nearby_competitors(business_type: BusinessType, canonical: CanonicalProfile) -> list[NearbyCompetitor]:
    """Returns the three most popular nearby businesses of the same type, the business itself left out."""
    own_type = canonical.primary_type if canonical.primary_type not in GENERIC_PLACE_TYPES else None
    place_types = TYPE_PLACE_TYPES.get(business_type) or ([own_type] if own_type else [])
    if not place_types or canonical.lat is None or canonical.lng is None:
        return []
    body = {
        "includedTypes": place_types,
        "maxResultCount": NEARBY_COUNT + 1,
        "rankPreference": "POPULARITY",
        "locationRestriction": {
            "circle": {"center": {"latitude": canonical.lat, "longitude": canonical.lng}, "radius": NEARBY_RADIUS_METERS}
        },
    }
    data = await places_request("POST", "places:searchNearby", NEARBY_FIELD_MASK, body)
    competitors = [
        NearbyCompetitor(
            place_id=place["id"],
            name=(place.get("displayName") or {}).get("text", ""),
            review_count=place.get("userRatingCount"),
            rating=place.get("rating"),
        )
        for place in data.get("places", [])
        if place["id"] != canonical.place_id
    ]
    return competitors[:NEARBY_COUNT]
