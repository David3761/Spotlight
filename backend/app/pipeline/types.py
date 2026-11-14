"""Internal pipeline data stored on the scan row, never sent to the frontend as is."""

from typing import Literal

from pydantic import BaseModel

from app.models import Problem


class ClaimedProblem(BaseModel):
    """A problem the owner marked as fixed, kept so it can be reopened."""

    problem: Problem
    score_added: int


class ScanInternal(BaseModel):
    """The `internal` JSON of a scan: where its report came from and what resolving needs."""

    source: Literal["fixture", "pipeline"]
    claimed_problems: dict[str, ClaimedProblem] = {}
