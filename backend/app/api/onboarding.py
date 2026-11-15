"""The onboarding chat endpoint."""

from fastapi import APIRouter

from app.errors import ERROR_RESPONSES
from app.models import OnboardingTurn, OnboardingTurnRequest
from app.services.onboarding import get_onboarding_turn

router = APIRouter(tags=["onboarding"], responses=ERROR_RESPONSES)
"""The onboarding routes."""


@router.post("/api/onboarding/turn")
async def post_turn(request: OnboardingTurnRequest) -> OnboardingTurn:
    """Returns the assistant's next onboarding message and the answers collected so far."""
    return await get_onboarding_turn(request.messages, request.answers)
