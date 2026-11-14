"""Checks the overall score formula."""

from app.pipeline.scoring import get_gemini_score, get_overall_exact


def test_design_scores_give_42_2() -> None:
    """Checks that the design's chapter scores and Gemini score give the design's overall score."""
    scores = {
        "profil": 65,
        "recenzii": 50,
        "continut": 35,
        "site": 50,
        "info": 35,
        "mentiuni": 25,
        "social": 55,
        "cunoaste": 20,
    }
    assert get_overall_exact(scores, 17) == 42.2


def test_unknown_scores_are_renormalized() -> None:
    """Checks that chapters without a score and an unknown Gemini test are left out of the weights."""
    scores = {
        "profil": 50,
        "recenzii": None,
        "continut": None,
        "site": None,
        "info": None,
        "mentiuni": None,
        "social": None,
        "cunoaste": None,
    }
    assert get_overall_exact(scores, None) == 50.0


def test_gemini_score_averages_position_over_every_question() -> None:
    """Checks the live-test score: named first in 2 of 12 questions with correct facts gives 29."""
    positions = [1, 1] + [None] * 10
    assert get_gemini_score(positions, facts_ok=True) == 29
    assert get_gemini_score([None] * 12, facts_ok=None) == 0
    assert get_gemini_score([1] * 12, facts_ok=True) == 100
