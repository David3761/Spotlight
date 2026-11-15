"""Scan-side API models from `docs/contract.md`, plus the facts both devs' backend code shares."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

ChapterId = Literal["profil", "recenzii", "continut", "site", "info", "mentiuni", "social", "cunoaste"]
"""The eight report chapters, in display order."""

StepId = Literal["google", "recenzii", "website", "retele", "gemini"]
"""The five progress steps on the loading screen."""

CheckStatus = Literal["pass", "partial", "fail", "unknown"]
"""The outcome of one check."""

FixType = Literal["generate", "owner_action", "dev_export"]
"""Who fixes a problem: generated text, the owner by hand, or the web developer."""

FixPanel = Literal["generate_text", "info_page", "steps", "dev_export"]
"""The side panel a problem opens."""

Tone = Literal["prietenos", "profesionist", "scurt"]
"""The tone of a generated text."""

BusinessType = Literal["cafenea", "restaurant", "bar", "salon", "hotel", "magazin", "altceva"]
"""The business type picked in onboarding."""

Platform = Literal["tripadvisor", "glovo", "wolt", "bolt_food", "booking", "booksy"]
"""The other platforms a business can say it is listed on."""

YesNoUnknown = Literal["da", "nu", "nu_stiu"]
"""A self-reported yes / no / don't know answer."""

PostRecency = Literal["luna_asta", "mai_demult", "niciodata", "nu_stiu"]
"""A self-reported answer about the last post."""

ErrorCode = Literal[
    "unreadable_link",
    "place_not_found",
    "scan_not_found",
    "scan_running",
    "check_not_found",
    "upstream_error",
    "invalid_phone",
    "alerts_off",
    "no_reviews",
]
"""The error codes the API returns."""


class ErrorBody(BaseModel):
    """The code and Romanian message of an API error."""

    code: ErrorCode
    message_ro: str


class ErrorResponse(BaseModel):
    """The body of every error response."""

    error: ErrorBody


class PlaceSearchRequest(BaseModel):
    """The onboarding answers used to search for the business on Google."""

    business_name: str
    city: str
    neighborhood: str


class PlaceCandidate(BaseModel):
    """A Google place that may be the owner's business."""

    place_id: str
    name: str
    address: str
    type_label_ro: str
    rating: float | None
    review_count: int | None
    best: bool


class PlaceSearchResponse(BaseModel):
    """Up to five candidates, best match first."""

    candidates: list[PlaceCandidate]


class ResolveLinkRequest(BaseModel):
    """A Google Maps link pasted by the owner."""

    url: str


class SelfReport(BaseModel):
    """The owner's answers to questions no API can answer."""

    profile_claimed: YesNoUnknown | None
    has_google_description: YesNoUnknown | None
    last_google_post: PostRecency | None
    last_social_post: PostRecency | None


class ScanInputs(BaseModel):
    """Everything the onboarding collects before a scan starts."""

    business_name: str
    business_type: BusinessType
    business_type_label_ro: str
    city: str
    neighborhood: str
    has_website: bool
    website_url: str | None
    place_id: str | None
    maps_url: str | None
    no_google_profile: bool
    instagram_url: str | None
    tiktok_url: str | None
    platforms: list[Platform] | None
    self_report: SelfReport


class ScanCreated(BaseModel):
    """The ID of a scan that has just started."""

    scan_id: str


OnboardingField = Literal[
    "business_name",
    "business_type",
    "city",
    "neighborhood",
    "website",
    "google_profile",
    "profile_claimed",
    "has_google_description",
    "last_google_post",
    "social",
    "last_social_post",
    "platforms",
]
"""An answer the onboarding assistant collects, in the order it asks for them."""

GoogleChoice = Literal["place", "none", "later"]
"""How the owner answered the Google Maps step: a place picked or linked, no profile, or adding it later."""


class OnboardingAnswers(BaseModel):
    """What the onboarding has collected so far; `None` means not answered yet."""

    business_name: str | None
    business_type: BusinessType | None
    business_type_label_ro: str | None
    city: str | None
    neighborhood: str | None
    has_website: bool | None
    website_url: str | None
    google_choice: GoogleChoice | None
    place: PlaceCandidate | None
    maps_url: str | None
    self_report: SelfReport
    has_social: bool | None
    instagram_url: str | None
    tiktok_url: str | None
    platforms: list[Platform] | None


class OnboardingMessage(BaseModel):
    """One message of the onboarding chat."""

    role: Literal["assistant", "user"]
    text: str = Field(max_length=2000)


class OnboardingTurnRequest(BaseModel):
    """The onboarding chat so far, the owner's newest message last, with the answers collected before it."""

    messages: list[OnboardingMessage] = Field(min_length=1)
    answers: OnboardingAnswers


class OnboardingTurn(BaseModel):
    """The assistant's next message, with the answers collected and still missing after the owner's newest message."""

    reply_ro: str
    answers: OnboardingAnswers
    missing: list[OnboardingField]
    candidates: list[PlaceCandidate]


class StepEvent(BaseModel):
    """A progress step that started or finished."""

    type: Literal["step"]
    step: StepId
    status: Literal["running", "done"]
    detail_ro: str | None


class CompleteEvent(BaseModel):
    """The last event of a scan that produced a report."""

    type: Literal["complete"]
    scan_id: str


class FailedEvent(BaseModel):
    """The last event of a scan that could not produce a report."""

    type: Literal["failed"]
    message_ro: str


ScanEvent = Annotated[StepEvent | CompleteEvent | FailedEvent, Field(discriminator="type")]
"""One event on the scan progress stream."""


class Business(BaseModel):
    """The business a report is about."""

    name: str
    initials: str
    type: BusinessType
    type_label_ro: str
    city: str
    neighborhood: str
    place_id: str | None
    address: str | None
    phone: str | None
    website: str | None
    google_maps_uri: str | None
    instagram_url: str | None
    instagram_handle: str | None
    tiktok_url: str | None


class FixPayload(BaseModel):
    """What the fix panel of a problem shows."""

    panel: FixPanel
    steps_ro: list[str]
    deep_link: str | None
    deep_link_label_ro: str | None
    where_ro: str | None
    max_chars: int | None
    evidence_ro: str | None


class Problem(BaseModel):
    """An open problem the owner can fix."""

    check_id: str
    chapter_id: ChapterId
    chapter_name_ro: str
    title_ro: str
    why_ro: str
    points: int
    impact: float
    fix_type: FixType
    fix: FixPayload


class SolvedItem(BaseModel):
    """A check that passed or that the owner marked as fixed."""

    check_id: str
    title_ro: str
    source: Literal["passed", "claimed_fixed"]
    points: int | None


class UnknownItem(BaseModel):
    """A check that could not run, with the reason."""

    check_id: str
    title_ro: str
    reason_ro: str


class Chapter(BaseModel):
    """One of the eight report chapters."""

    id: ChapterId
    name_ro: str
    intro_ro: str
    where_to_fix_ro: str | None
    score: int | None
    weight: float
    possible_points: int
    overall_gain_if_all_fixed: int
    has_fixes: bool
    problems: list[Problem]
    solved: list[SolvedItem]
    unknown: list[UnknownItem]


class Source(BaseModel):
    """A source Gemini cited in an answer."""

    title: str
    uri: str
    kind: Literal["maps", "web"]


class GeminiPrompt(BaseModel):
    """One customer question asked to Gemini and how it answered."""

    text: str
    mentioned: bool
    runs_mentioned: int
    runs: int
    others: list[str]
    answer_excerpt: str
    sources: list[Source]


class GeminiGroup(BaseModel):
    """A group of four related customer questions."""

    id: Literal["general", "cartier", "situatii"]
    name_ro: str
    desc_ro: str
    mentioned: int
    total: int
    prompts: list[GeminiPrompt]


class TopCompetitor(BaseModel):
    """A business Gemini recommended instead, with how often."""

    name: str
    place_id: str | None
    mentions: int


class GeminiBlock(BaseModel):
    """The result of the live Gemini test."""

    status: Literal["complete", "unknown"]
    score: int | None
    weight: float
    mentioned: int
    total: int
    last_checked: str
    top_competitors: list[TopCompetitor]
    groups: list[GeminiGroup]


class CompareRow(BaseModel):
    """One business in the comparison table."""

    name: str
    place_id: str | None
    review_count: int | None
    rating: float | None
    photo_count: int | None
    photo_count_capped: bool
    hours_complete: bool | None


class ComparisonAction(BaseModel):
    """A button under the comparison that opens a problem."""

    label_ro: str
    check_id: str
    chapter_id: ChapterId


class Comparison(BaseModel):
    """The owner's business next to the rivals Gemini recommends."""

    me: CompareRow
    rivals: list[CompareRow]
    insights_ro: list[str]
    actions: list[ComparisonAction]


class Report(BaseModel):
    """The full result of a scan."""

    scan_id: str
    checked_at: str
    business: Business
    overall: int
    overall_exact: float
    summary_ro: str
    open_problem_count: int
    next_steps: list[Problem]
    gemini: GeminiBlock
    chapters: list[Chapter]
    comparison: Comparison


class ScanEnvelope(BaseModel):
    """A scan's status and, once complete, its report."""

    scan_id: str
    status: Literal["running", "complete", "failed"]
    report: Report | None
    error_ro: str | None


class ScoreUpdate(BaseModel):
    """The new scores after a problem is marked as fixed or unmarked."""

    chapter_id: ChapterId
    chapter_score: int
    chapter_points_added: int
    overall: int
    overall_exact: float
    overall_delta: float
    report: Report


class FaqItem(BaseModel):
    """A question and its answer."""

    q: str
    a: str


class WebsiteFacts(BaseModel):
    """Facts read from the business website."""

    what_it_is: str | None
    menu_items_or_services: list[str]
    prices_present: bool
    faq_items: list[FaqItem]
    language: str | None


class Facts(BaseModel):
    """Everything fix texts and the info page are written from."""

    name: str
    type_label_ro: str
    city: str
    neighborhood: str
    address: str | None
    phone: str | None
    website: str | None
    google_maps_uri: str | None
    hours_ro: list[str]
    special_hours_ro: list[str]
    attributes_ro: list[str]
    instagram_handle: str | None
    tiktok_url: str | None
    platforms_ro: list[str]
    website_facts: WebsiteFacts | None
