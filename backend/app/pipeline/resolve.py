"""Step 1: finding the owner's business on Google, by search or from a Google Maps link."""

import re
from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlparse

import httpx

from app.errors import ApiError
from app.models import PlaceCandidate
from app.pipeline.normalize import names_match, names_overlap
from app.pipeline.places_api import places_request

SEARCH_FIELD_MASK = ",".join(
    f"places.{field}"
    for field in ["id", "displayName", "shortFormattedAddress", "primaryTypeDisplayName", "rating", "userRatingCount"]
)
"""The Text Search fields a candidate card needs."""

MAX_CANDIDATES = 5
"""How many candidates the search returns."""

LINK_BIAS_RADIUS_METERS = 200.0
"""How far from a link's coordinates a matching place may be."""

LINK_TIMEOUT_SECONDS = 10
"""How long following a Maps link's redirects may take."""

SHORT_LINK_HOSTS = {"maps.app.goo.gl", "goo.gl"}
"""Google's short-link hosts for Maps links."""

MAX_REDIRECTS = 6
"""How many redirects a Maps link may take."""

CONSENT_HOST = "consent.google.com"
"""The host Google redirects European visitors to; the real URL is in its `continue` parameter."""


def get_candidate(place: dict[str, Any], best: bool) -> PlaceCandidate:
    """Returns a candidate card from a Text Search place."""
    return PlaceCandidate(
        place_id=place["id"],
        name=(place.get("displayName") or {}).get("text", ""),
        address=place.get("shortFormattedAddress", ""),
        type_label_ro=(place.get("primaryTypeDisplayName") or {}).get("text", ""),
        rating=place.get("rating"),
        review_count=place.get("userRatingCount"),
        best=best,
    )


async def search_places(business_name: str, city: str, neighborhood: str) -> list[PlaceCandidate]:
    """Returns up to five places for the owner's answers, best match first; the first is „best” when its name matches."""
    query = " ".join(part for part in (business_name, neighborhood, city) if part.strip())
    data = await places_request("POST", "places:searchText", SEARCH_FIELD_MASK, {"textQuery": query, "pageSize": MAX_CANDIDATES})
    places = data.get("places", [])[:MAX_CANDIDATES]
    return [
        get_candidate(place, index == 0 and names_overlap(business_name, (place.get("displayName") or {}).get("text", "")))
        for index, place in enumerate(places)
    ]


async def resolve_link(url: str) -> PlaceCandidate:
    """Returns the place a Google Maps link points to, or raises `ApiError("unreadable_link")`."""
    final_url = await get_final_url(url)
    place_id = get_link_place_id(final_url)
    if place_id:
        data = await places_request("GET", f"places/{place_id}", SEARCH_FIELD_MASK.replace("places.", ""))
        return get_candidate(data, best=True)
    name, coordinates = get_link_name_and_coordinates(final_url)
    if not name or not coordinates:
        raise ApiError("unreadable_link")
    latitude, longitude = coordinates
    body = {
        "textQuery": name,
        "pageSize": MAX_CANDIDATES,
        "locationBias": {"circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": LINK_BIAS_RADIUS_METERS}},
    }
    data = await places_request("POST", "places:searchText", SEARCH_FIELD_MASK, body)
    for place in data.get("places", []):
        if names_match(name, (place.get("displayName") or {}).get("text", "")):
            return get_candidate(place, best=True)
    raise ApiError("unreadable_link")


def is_google_maps_host(url: str) -> bool:
    """Returns whether a URL is on a Google Maps or Google short-link host, the only hosts the server will fetch."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    is_google = (
        host in SHORT_LINK_HOSTS
        or re.fullmatch(r"(www\.|maps\.|consent\.)?google\.(com|[a-z]{2}|co\.[a-z]{2}|com\.[a-z]{2})", host) is not None
    )
    return parsed.scheme in ("http", "https") and is_google


async def get_final_url(url: str) -> str:
    """Returns where a Maps link leads after its redirects, unwrapped from Google's consent page.

    Every hop must stay on a Google host, so a pasted link can't make the server fetch anything else.
    """
    current = url.strip()
    async with httpx.AsyncClient(follow_redirects=False, timeout=LINK_TIMEOUT_SECONDS) as client:
        for _ in range(MAX_REDIRECTS):
            if not is_google_maps_host(current):
                raise ApiError("unreadable_link")
            parsed = urlparse(current)
            if parsed.hostname == CONSENT_HOST:
                return parse_qs(parsed.query).get("continue", [current])[0]
            try:
                response = await client.get(current, headers={"User-Agent": "Mozilla/5.0"})
            except httpx.HTTPError as error:
                raise ApiError("unreadable_link") from error
            if not response.is_redirect:
                return current
            current = str(response.next_request.url) if response.next_request else current
    raise ApiError("unreadable_link")


def get_link_place_id(url: str) -> str | None:
    """Returns the Google place ID a Maps URL names directly (`query_place_id=` or `place_id:`), if any."""
    query = parse_qs(urlparse(url).query)
    if query.get("query_place_id"):
        return query["query_place_id"][0]
    match = re.search(r"place_id:([A-Za-z0-9_-]+)", unquote_plus(url))
    return match.group(1) if match else None


def get_link_name_and_coordinates(url: str) -> tuple[str | None, tuple[float, float] | None]:
    """Returns the place name and coordinates in a `/maps/place/<name>/@lat,lng` URL; exact pin coordinates win."""
    path = urlparse(url).path
    name_match = re.search(r"/place/([^/]+)", path)
    name = unquote_plus(unquote_plus(name_match.group(1))) if name_match else None
    pin = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    view = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    found = pin or view
    coordinates = (float(found.group(1)), float(found.group(2))) if found else None
    return name, coordinates
