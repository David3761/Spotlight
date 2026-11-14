"""Request and response models for the assistant conversations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models import ScoreUpdate

ChapterId = Literal[
    "profil", "recenzii", "continut", "site", "info", "mentiuni", "social", "cunoaste"
]
"""The ids of the report chapters."""

ConversationKind = Literal["onboarding", "assistant"]
"""The two kinds of conversation."""


class ProposedItem(BaseModel):
    """One problem the assistant proposes to mark as solved."""

    check_id: str
    title_ro: str
    points: int


class ActionOption(BaseModel):
    """One button under a proposed action; empty `check_ids` means the owner declines."""

    id: str
    label_ro: str
    check_ids: list[str]


class ProposedAction(BaseModel):
    """A change the assistant proposes and the owner confirms, declines or undoes."""

    action_id: str
    type: Literal["mark_resolved"] = "mark_resolved"
    items: list[ProposedItem]
    options: list[ActionOption]
    status: Literal["pending", "confirmed", "declined", "undone"] = "pending"
    confirmed_check_ids: list[str] = Field(default_factory=list)


class Message(BaseModel):
    """One message in a conversation, optionally carrying a proposed action and quick replies."""

    id: str
    role: Literal["user", "assistant"]
    text: str
    created_at: datetime
    action: ProposedAction | None = None
    chips: list[str] = Field(default_factory=list)


class Conversation(BaseModel):
    """A conversation with all its messages."""

    cid: str
    scan_id: str
    kind: ConversationKind
    title: str
    chapter_id: ChapterId | None
    messages: list[Message]


class ConversationSummary(BaseModel):
    """One row of the conversation list."""

    cid: str
    kind: ConversationKind
    title: str
    chapter_id: ChapterId | None
    chapter_name_ro: str | None
    preview: str
    solved_count: int
    updated_at: datetime


class ConversationList(BaseModel):
    """The conversations of a scan, newest first."""

    conversations: list[ConversationSummary]


class CreateConversationRequest(BaseModel):
    """The body of a request that creates a conversation."""

    kind: ConversationKind
    chapter_id: ChapterId | None = None
    title: str | None = None
    messages: list[Message] | None = None


class CreateConversationResponse(BaseModel):
    """The id of the conversation that was created."""

    cid: str


class PostMessageRequest(BaseModel):
    """The body of a request that sends the owner's message to the assistant."""

    text: str


class PostMessageResponse(BaseModel):
    """The assistant's reply to a message."""

    reply: Message


class ActionRequest(BaseModel):
    """The body of a request that confirms, declines or undoes a proposed action."""

    option_id: str


class ActionResult(BaseModel):
    """The outcome of an action: its new state, the updated scores and the assistant's follow-up."""

    action: ProposedAction
    score: ScoreUpdate | None
    followup: Message | None
