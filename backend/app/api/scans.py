"""Scan endpoints: start, progress stream, status, rescan, „Am rezolvat” and the Gemini re-test."""

from collections.abc import AsyncIterator

from fastapi import APIRouter
from pydantic import RootModel
from sse_starlette import EventSourceResponse

from app.errors import ERROR_RESPONSES
from app.models import (
    Report,
    ScanCreated,
    ScanEnvelope,
    ScanEvent,
    ScanInputs,
    ScoreUpdate,
)
from app.services import scans
from app.services.resolution import mark_resolved

router = APIRouter(tags=["scans"], responses=ERROR_RESPONSES)
"""The scan routes."""


class ScanEventMessage(RootModel[ScanEvent]):
    """One SSE `data:` payload, documented so the frontend gets the event types."""


@router.post("/api/scans")
async def start_scan(inputs: ScanInputs) -> ScanCreated:
    """Starts a scan for the onboarding inputs; async so the scan task starts on the server's event loop."""
    return ScanCreated(scan_id=scans.create_scan(inputs))


@router.get(
    "/api/scans/{scan_id}/events",
    response_class=EventSourceResponse,
    responses={200: {"model": ScanEventMessage, "description": "One JSON `ScanEvent` per `data:` line."}},
)
def stream_events(scan_id: str) -> EventSourceResponse:
    """Streams the scan's progress as Server-Sent Events."""
    events = scans.get_events(scan_id)

    async def get_messages() -> AsyncIterator[dict[str, str]]:
        """Yields each event as an SSE message."""
        async for event in events:
            yield {"data": event.model_dump_json()}

    return EventSourceResponse(get_messages())


@router.get("/api/scans/{scan_id}")
def get_scan(scan_id: str) -> ScanEnvelope:
    """Returns the scan's status and, once complete, its report."""
    return scans.get_envelope(scan_id)


@router.post("/api/scans/{scan_id}/rescan")
async def rescan(scan_id: str) -> ScanCreated:
    """Starts a new scan with the same inputs; async so the scan task starts on the server's event loop."""
    return ScanCreated(scan_id=scans.rescan(scan_id))


@router.post("/api/scans/{scan_id}/problems/{check_id}/resolve")
def resolve_problem(scan_id: str, check_id: str) -> ScoreUpdate:
    """Marks a problem as fixed by the owner and returns the new scores."""
    return mark_resolved(scan_id, [check_id])


@router.post("/api/scans/{scan_id}/gemini-test")
async def run_gemini_test(scan_id: str) -> Report:
    """Reruns only the live Gemini test and returns the updated report."""
    return await scans.run_gemini_test(scan_id)
