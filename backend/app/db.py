"""SQLite storage for scans and assistant conversations."""

from datetime import datetime

from sqlmodel import Field, Session, SQLModel, create_engine

from app.config import BACKEND_DIR

engine = create_engine(f"sqlite:///{BACKEND_DIR / 'app.db'}", connect_args={"check_same_thread": False})
"""The engine for `backend/app.db`."""


class ScanRow(SQLModel, table=True):
    """A scan with its inputs, internal pipeline data and final report, stored as JSON text."""

    __tablename__ = "scans"

    id: str = Field(primary_key=True)
    created_at: datetime
    status: str
    inputs: str
    internal: str = "{}"
    report: str | None = None
    error: str | None = None


class ConversationRow(SQLModel, table=True):
    """An onboarding or assistant conversation, stored as JSON text."""

    __tablename__ = "conversations"

    id: str = Field(primary_key=True)
    scan_id: str = Field(index=True)
    kind: str
    title: str
    chapter_id: str | None = None
    messages: str = "[]"
    pending_actions: str = "[]"
    created_at: datetime
    updated_at: datetime


def create_tables() -> None:
    """Creates the tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Returns a new session; use it as `with get_session() as session:`."""
    return Session(engine)
