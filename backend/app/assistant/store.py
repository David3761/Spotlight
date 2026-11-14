"""Reads and writes conversations in the `conversations` table."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import literal_column
from sqlmodel import select

from app.assistant.schemas import (
    Conversation,
    ConversationSummary,
    Message,
    ProposedAction,
)
from app.db import ConversationRow, get_session
from app.services.resolution import load_report

DEFAULT_TITLE = "Conversație nouă"
"""The title of a conversation until the owner's first message names it."""

ONBOARDING_CHAPTER_NAME = "Configurare"
"""The chapter name shown for the onboarding conversation."""

MAX_TITLE_CHARS = 60
"""The longest title taken from a first message."""

MAX_PREVIEW_CHARS = 80
"""The longest message excerpt shown in the conversation list."""

MESSAGES_ADAPTER = TypeAdapter(list[Message])
"""Converts a list of messages to and from the JSON text stored in the row."""

ACTIONS_ADAPTER = TypeAdapter(list[ProposedAction])
"""Converts a list of proposed actions to and from the JSON text stored in the row."""


def create_conversation(
    scan_id: str,
    kind: str,
    chapter_id: str | None,
    title: str | None,
    messages: list[Message],
) -> str:
    """Creates a conversation with the given messages and returns its id."""
    now = datetime.now(UTC)
    cid = uuid4().hex
    row = ConversationRow(
        id=cid,
        scan_id=scan_id,
        kind=kind,
        title=title or DEFAULT_TITLE,
        chapter_id=chapter_id,
        messages=MESSAGES_ADAPTER.dump_json(messages).decode(),
        pending_actions=ACTIONS_ADAPTER.dump_json([message.action for message in messages if message.action]).decode(),
        created_at=now,
        updated_at=now,
    )
    with get_session() as session:
        session.add(row)
        session.commit()
    return cid


def get_conversation(cid: str) -> Conversation | None:
    """Returns the conversation with its messages, or `None` when the id is unknown."""
    with get_session() as session:
        row = session.get(ConversationRow, cid)
        if row is None:
            return None
        return Conversation(
            cid=row.id,
            scan_id=row.scan_id,
            kind=row.kind,
            title=row.title,
            chapter_id=row.chapter_id,
            messages=MESSAGES_ADAPTER.validate_json(row.messages),
        )


def get_action(cid: str, action_id: str) -> ProposedAction | None:
    """Returns a stored action of the conversation, or `None` when there is no such action."""
    with get_session() as session:
        row = session.get(ConversationRow, cid)
        if row is None:
            return None
        actions = ACTIONS_ADAPTER.validate_json(row.pending_actions)
        return next((action for action in actions if action.action_id == action_id), None)


def append_messages(cid: str, messages: list[Message]) -> None:
    """Appends messages to the conversation, stores their actions and names it after the first user message."""
    with get_session() as session:
        row = session.get(ConversationRow, cid)
        if row is None:
            return
        stored = MESSAGES_ADAPTER.validate_json(row.messages)
        actions = ACTIONS_ADAPTER.validate_json(row.pending_actions)
        for message in messages:
            if message.action:
                actions.append(message.action)
            if message.role == "user" and message.text.strip() and row.title == DEFAULT_TITLE:
                row.title = get_shortened(message.text, MAX_TITLE_CHARS)
        row.messages = MESSAGES_ADAPTER.dump_json(stored + messages).decode()
        row.pending_actions = ACTIONS_ADAPTER.dump_json(actions).decode()
        row.updated_at = datetime.now(UTC)
        session.add(row)
        session.commit()


def update_action(cid: str, action: ProposedAction, chapter_id: str | None = None) -> None:
    """Replaces the stored action and its copy in the message, and sets the chapter when none is set yet."""
    with get_session() as session:
        row = session.get(ConversationRow, cid)
        if row is None:
            return
        stored = MESSAGES_ADAPTER.validate_json(row.messages)
        for message in stored:
            if message.action and message.action.action_id == action.action_id:
                message.action = action
        actions = [
            action if candidate.action_id == action.action_id else candidate
            for candidate in ACTIONS_ADAPTER.validate_json(row.pending_actions)
        ]
        row.messages = MESSAGES_ADAPTER.dump_json(stored).decode()
        row.pending_actions = ACTIONS_ADAPTER.dump_json(actions).decode()
        if chapter_id and row.chapter_id is None:
            row.chapter_id = chapter_id
        row.updated_at = datetime.now(UTC)
        session.add(row)
        session.commit()


def get_summaries(scan_id: str) -> list[ConversationSummary]:
    """Returns the scan's conversations as list rows, newest first."""
    with get_session() as session:
        rows = session.exec(
            select(ConversationRow)
            .where(ConversationRow.scan_id == scan_id)
            .order_by(ConversationRow.updated_at.desc(), literal_column("rowid").desc())
        ).all()

    chapter_names = {}
    if any(row.kind != "onboarding" and row.chapter_id for row in rows):
        chapter_names = {chapter.id: chapter.name_ro for chapter in load_report(scan_id).chapters}

    summaries = []
    for row in rows:
        messages = MESSAGES_ADAPTER.validate_json(row.messages)
        actions = ACTIONS_ADAPTER.validate_json(row.pending_actions)
        summaries.append(
            ConversationSummary(
                cid=row.id,
                kind=row.kind,
                title=row.title,
                chapter_id=row.chapter_id,
                chapter_name_ro=(ONBOARDING_CHAPTER_NAME if row.kind == "onboarding" else chapter_names.get(row.chapter_id)),
                preview=get_preview(messages),
                solved_count=sum(len(action.confirmed_check_ids) for action in actions if action.status == "confirmed"),
                updated_at=row.updated_at.replace(tzinfo=UTC),
            )
        )
    return summaries


def get_preview(messages: list[Message]) -> str:
    """Returns the last message prefixed with its author, shortened for the conversation list."""
    if not messages:
        return ""
    last = messages[-1]
    author = "Asistent" if last.role == "assistant" else "Tu"
    return f"{author}: {get_shortened(last.text, MAX_PREVIEW_CHARS)}"


def get_shortened(text: str, max_chars: int) -> str:
    """Returns the text on one line, cut with an ellipsis when it is longer than the limit."""
    one_line = " ".join(text.split())
    if len(one_line) <= max_chars:
        return one_line
    return one_line[: max_chars - 1].rstrip() + "…"
