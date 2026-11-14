"""Onboarding endpoints that find the business on Google."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models import PlaceCandidate, PlaceSearchRequest, PlaceSearchResponse, ResolveLinkRequest

router = APIRouter(tags=["places"], responses=ERROR_RESPONSES)
"""The place routes."""

STUB_CANDIDATES = [
    PlaceCandidate(
        place_id="ChIJ-mock-cafeneaua-boema",
        name="Cafeneaua Boema",
        address="Str. Dr. Lister, Cotroceni",
        type_label_ro="Cafenea",
        rating=4.6,
        review_count=38,
        best=True,
    ),
    PlaceCandidate(
        place_id="ChIJ-mock-boema-bistro",
        name="Boema Bistro",
        address="Calea Moșilor, Sector 2",
        type_label_ro="Restaurant",
        rating=4.3,
        review_count=112,
        best=False,
    ),
    PlaceCandidate(
        place_id="ChIJ-mock-boem-coffee-corner",
        name="Boem Coffee Corner",
        address="Bd. Unirii, Sector 4",
        type_label_ro="Cafenea",
        rating=4.1,
        review_count=19,
        best=False,
    ),
]
"""The candidates from the onboarding artboard, served until the Places search is connected."""


@router.post("/api/places/search")
def search_places(_: PlaceSearchRequest) -> PlaceSearchResponse:
    """Returns up to five Google places that may be the business, best match first."""
    return PlaceSearchResponse(candidates=STUB_CANDIDATES)


@router.post("/api/places/resolve-link")
def resolve_link(_: ResolveLinkRequest) -> PlaceCandidate:
    """Returns the Google place a Maps link points to."""
    return STUB_CANDIDATES[0]
