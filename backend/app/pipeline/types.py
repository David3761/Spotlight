"""Internal pipeline data stored on the scan row, never sent to the frontend as is."""

from typing import Literal

from pydantic import BaseModel

from app.models import ChapterId, CheckStatus, WebsiteFacts
from app.pipeline.canonical import CanonicalProfile


class Evidence(BaseModel):
    """What a check found, what it expected and where it looked."""

    found: str | None = None
    expected: str | None = None
    url: str | None = None


class CheckResult(BaseModel):
    """The outcome of one check, with its points and evidence."""

    check_id: str
    chapter_id: ChapterId
    status: CheckStatus
    points_earned: float
    points_max: float
    claimed_fixed: bool = False
    gate: bool = False
    evidence: Evidence = Evidence()
    params: dict[str, str] = {}
    reason_ro: str | None = None


class ScanInternal(BaseModel):
    """The `internal` JSON of a scan: where its report came from and the check results it was scored from."""

    source: Literal["fixture", "pipeline"]
    checks: list[CheckResult] = []
    canonical: CanonicalProfile | None = None
    website_facts: WebsiteFacts | None = None
