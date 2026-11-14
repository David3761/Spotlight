"""Checks the overall score formula."""

from app.pipeline.scoring import get_overall_exact


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
