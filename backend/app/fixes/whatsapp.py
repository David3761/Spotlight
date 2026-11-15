"""Sending WhatsApp text messages through the WhatsApp Cloud API, from the business number set in `.env`."""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

MESSAGES_URL = "https://graph.facebook.com/v23.0/{phone_number_id}/messages"
"""The Cloud API endpoint that sends a message from the business phone number."""

SEND_TIMEOUT_SECONDS = 15
"""How long one send may take."""

START_TEXT = "Start"
"""The text the owner sends us first; it opens the 24-hour window in which we may send them plain text messages."""


class WhatsAppError(Exception):
    """Raised when WhatsApp isn't set up or refuses a message (for example when the 24-hour window is closed)."""


def is_configured() -> bool:
    """Returns whether `.env` has everything needed to send WhatsApp messages."""
    settings = get_settings()
    return bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id and settings.whatsapp_business_number)


def get_start_link() -> str | None:
    """Returns the wa.me link that opens a chat with our business number with „Start” typed in, or `None` when not set up.

    The number keeps only its digits, so spaces and dashes don't break the link. It isn't validated, because Meta's
    test numbers (+1 555 …) don't pass phone-number validation.
    """
    if not is_configured():
        return None
    digits = "".join(char for char in get_settings().whatsapp_business_number if char.isdigit())
    return f"https://wa.me/{digits}?text={START_TEXT}"


async def send_text(phone_e164: str, text: str) -> None:
    """Sends a plain text message to a phone number; raises `WhatsAppError` when WhatsApp isn't set up or refuses it.

    Plain text only reaches someone who wrote to our number in the last 24 hours. The token travels in a header, so it
    never shows up in a logged URL.
    """
    settings = get_settings()
    if not is_configured():
        raise WhatsAppError("WhatsApp is not configured")
    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_e164.lstrip("+"),
        "type": "text",
        "text": {"body": text},
    }
    try:
        async with httpx.AsyncClient(timeout=SEND_TIMEOUT_SECONDS) as client:
            response = await client.post(
                MESSAGES_URL.format(phone_number_id=settings.whatsapp_phone_number_id),
                json=body,
                headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
            )
    except httpx.HTTPError as error:
        raise WhatsAppError(type(error).__name__) from error
    if response.status_code != 200:
        payload = response.json() if "json" in response.headers.get("content-type", "") else None
        error = payload.get("error") if isinstance(payload, dict) else None
        message = error.get("message") if isinstance(error, dict) else None
        logger.info("WhatsApp refused a message: %s %s", response.status_code, message)
        raise WhatsAppError(message or f"HTTP {response.status_code}")
