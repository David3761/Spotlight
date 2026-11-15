"""API errors in the contract's format, and the handlers that render them."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.models import ErrorBody, ErrorCode, ErrorResponse

ERROR_STATUS: dict[ErrorCode, int] = {
    "unreadable_link": 422,
    "place_not_found": 404,
    "scan_not_found": 404,
    "scan_running": 409,
    "check_not_found": 404,
    "upstream_error": 502,
    "invalid_phone": 422,
    "alerts_off": 409,
    "no_reviews": 404,
}
"""The HTTP status of each error code."""

ERROR_MESSAGES_RO: dict[ErrorCode, str] = {
    "unreadable_link": "Nu am putut citi acest link.",
    "place_not_found": "Nu am găsit afacerea pe Google.",
    "scan_not_found": "Nu am găsit această analiză.",
    "scan_running": "Analiza încă rulează. Încearcă din nou peste câteva secunde.",
    "check_not_found": "Nu am găsit această problemă.",
    "upstream_error": "Un serviciu de care depindem nu a răspuns. Încearcă din nou.",
    "invalid_phone": "Numărul de telefon nu pare corect. Scrie-l așa: 0722 123 456.",
    "alerts_off": "Pornește mai întâi mesajele pe WhatsApp.",
    "no_reviews": "Nu am găsit încă nicio recenzie pe Google.",
}
"""The default Romanian message of each error code."""


class ApiError(Exception):
    """An error the API returns to the frontend with a contract error code."""

    def __init__(self, code: ErrorCode, message_ro: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.message_ro = message_ro or ERROR_MESSAGES_RO[code]


def handle_api_error(_: Request, error: ApiError) -> JSONResponse:
    """Renders an `ApiError` in the contract's error format."""
    body = ErrorResponse(error=ErrorBody(code=error.code, message_ro=error.message_ro))
    return JSONResponse(status_code=ERROR_STATUS[error.code], content=body.model_dump())


ERROR_RESPONSES = {status: {"model": ErrorResponse} for status in sorted(set(ERROR_STATUS.values()))}
"""The error responses every router documents in the OpenAPI schema."""
