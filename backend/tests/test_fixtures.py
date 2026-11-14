"""Checks that the demo fixtures match the contract models and the scoring rules."""

from app.jobs import get_fixture_checks
from app.models import Facts, Report
from app.pipeline.problems import build_chapters
from app.pipeline.scoring import refresh_report_totals
from app.services.resolution import DEMO_FACTS_FILE, DEMO_REPORT_FILE


def get_report() -> Report:
    """Returns the demo report as stored."""
    return Report.model_validate_json(DEMO_REPORT_FILE.read_text(encoding="utf-8"))


def test_report_is_what_the_rules_produce_from_its_checks() -> None:
    """Checks that rebuilding the demo report from its checks changes nothing, so every number in it is valid."""
    report = get_report()
    rebuilt = report.model_copy(deep=True)
    rebuilt.chapters = build_chapters(get_fixture_checks(), rebuilt.business)
    refresh_report_totals(rebuilt)
    assert rebuilt == report
    assert [chapter.id for chapter in report.chapters] == [
        "profil", "recenzii", "continut", "site", "info", "mentiuni", "social", "cunoaste",
    ]


def test_facts_fixture_validates() -> None:
    """Checks that the demo facts parse as `Facts`."""
    Facts.model_validate_json(DEMO_FACTS_FILE.read_text(encoding="utf-8"))
