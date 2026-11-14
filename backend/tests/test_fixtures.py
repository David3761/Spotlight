"""Checks that the demo fixtures match the contract models."""

from app.models import Facts, Report
from app.services.resolution import FIXTURES_DIR


def test_report_fixture_validates() -> None:
    """Checks that the demo report parses as a `Report` with the design's numbers."""
    report = Report.model_validate_json((FIXTURES_DIR / "boema_report.json").read_text(encoding="utf-8"))
    assert report.overall == 42
    assert report.open_problem_count == sum(len(chapter.problems) for chapter in report.chapters)
    assert [chapter.id for chapter in report.chapters] == [
        "profil",
        "recenzii",
        "continut",
        "site",
        "info",
        "mentiuni",
        "social",
        "cunoaste",
    ]


def test_facts_fixture_validates() -> None:
    """Checks that the demo facts parse as `Facts`."""
    Facts.model_validate_json((FIXTURES_DIR / "boema_facts.json").read_text(encoding="utf-8"))
