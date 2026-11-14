"""Request and response models for the fix text, info page and developer export endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models import FaqItem

Tone = Literal["prietenos", "profesionist", "scurt"]
"""The writing tones the owner can pick for a generated text."""


class GenerateRequest(BaseModel):
    """The body of a request for a generated fix text."""

    tone: Tone
    variant: int = Field(ge=0)


class GeneratedText(BaseModel):
    """A generated text for one problem, with the facts it includes."""

    check_id: str
    tone: Tone
    variant: int
    text: str
    included_ro: list[str]
    max_chars: int | None


class GeneratedTextDraft(BaseModel):
    """What the language model returns when it writes a fix text."""

    text: str
    included_ro: list[str]


class InfoPage(BaseModel):
    """The info page the owner puts on their website, with its downloadable HTML."""

    suggested_url: str
    title: str
    subtitle: str
    description: str
    address: str | None
    area_note: str | None
    hours: list[str]
    holiday_hours: str | None
    phone: str | None
    instagram: str | None
    also_on: list[str]
    menu: list[str]
    faq: list[FaqItem]
    to_fill: list[str]
    message_ro: str
    html: str


class InfoPageDraft(BaseModel):
    """What the language model writes for the info page: the parts that are not copied from the facts."""

    subtitle: str
    description: str
    faq_answers: list[str]
    message_ro: str


class DevExport(BaseModel):
    """The Markdown document and the note for the person who builds the website."""

    markdown: str
    message_ro: str
