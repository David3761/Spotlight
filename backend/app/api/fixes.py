"""Routes for generated fix texts, the info page and the developer export."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from google.genai.errors import APIError

from app.fixes.dev_export import get_dev_export
from app.fixes.generate import get_generated_text
from app.fixes.info_page import get_info_page
from app.fixes.schemas import DevExport, GeneratedText, GenerateRequest, InfoPage
from app.services.resolution import ScanNotFound


def get_error_response(status_code: int, code: str, message_ro: str) -> JSONResponse:
    """Returns a response with the contract's error body."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message_ro": message_ro}},
    )


class ContractErrorRoute(APIRoute):
    """A route that turns an unknown scan and a failed Gemini call into the contract's error bodies."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Returns the route handler wrapped so that known failures become error responses."""
        handler = super().get_route_handler()

        async def get_response(request: Request) -> Response:
            """Returns the handler's response, or the error response for a known failure."""
            try:
                return await handler(request)
            except ScanNotFound:
                return get_error_response(404, "scan_not_found", "Nu am găsit analiza asta.")
            except APIError:
                return get_error_response(502, "upstream_error", "Nu am putut contacta Gemini acum. Încearcă din nou.")

        return get_response


router = APIRouter(route_class=ContractErrorRoute)


@router.post("/api/scans/{scan_id}/fixes/{check_id}/generate", response_model=GeneratedText)
async def generate_fix_text(scan_id: str, check_id: str, request: GenerateRequest):
    """Returns the generated text for an open problem, or a 404 when the check is not one."""
    generated = await get_generated_text(scan_id, check_id, request.tone, request.variant)
    if generated is None:
        return get_error_response(404, "check_not_found", "Nu am găsit problema asta sau e deja rezolvată.")
    return generated


@router.get("/api/scans/{scan_id}/info-page", response_model=InfoPage)
async def read_info_page(scan_id: str):
    """Returns the info page for the scan."""
    return await get_info_page(scan_id)


@router.get("/api/scans/{scan_id}/dev-export", response_model=DevExport)
def read_dev_export(scan_id: str):
    """Returns the developer export for the scan."""
    return get_dev_export(scan_id)
