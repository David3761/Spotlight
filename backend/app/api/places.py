"""Onboarding endpoints that find the business on Google."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models import PlaceCandidate, PlaceSearchRequest, PlaceSearchResponse, ResolveLinkRequest
from app.pipeline.resolve import resolve_link, search_places

router = APIRouter(tags=["places"], responses=ERROR_RESPONSES)
"""The place routes."""


@router.post("/api/places/search")
async def search(request: PlaceSearchRequest) -> PlaceSearchResponse:
    """Returns up to five Google places that may be the business, best match first."""
    return PlaceSearchResponse(candidates=await search_places(request.business_name, request.city, request.neighborhood))


@router.post("/api/places/resolve-link")
async def resolve(request: ResolveLinkRequest) -> PlaceCandidate:
    """Returns the Google place a Maps link points to, or `422 unreadable_link`."""
    return await resolve_link(request.url)
