"""Tests for coageneration.evaluate."""

import pytest

from coageneration.core import CourseOfAction, Force
from coageneration.evaluate import coa_diversity, gbc_score, nash_gap, robustness_score


def _coa(coa_id: str, force: Force, mef: float = 0.5, actions: list | None = None) -> CourseOfAction:
    return CourseOfAction(
        coa_id=coa_id,
        force=force,
        actions=actions or [],
        objective="test objective",
        mef_score=mef,
    )


def test_gbc_score_equal_mef():
    blue = _coa("b", Force.BLUE, mef=0.5)
    red = _coa("r", Force.RED, mef=0.5)
    assert gbc_score(blue, red) == pytest.approx(0.5)


def test_gbc_score_blue_dominant():
    blue = _coa("b", Force.BLUE, mef=1.0)
    red = _coa("r", Force.RED, mef=0.0)
    assert gbc_score(blue, red) == pytest.approx(1.0)


def test_gbc_score_red_dominant():
    blue = _coa("b", Force.BLUE, mef=0.0)
    red = _coa("r", Force.RED, mef=1.0)
    assert gbc_score(blue, red) == pytest.approx(0.0)


def test_nash_gap_zero_sum():
    # Perfect zero-sum: blue + red == 1.0 => gap == 0
    assert nash_gap(0.6, 0.4) == pytest.approx(0.0)


def test_nash_gap_non_zero_sum():
    assert nash_gap(0.7, 0.7) == pytest.approx(0.4)


def test_robustness_score_min_mef():
    coa = _coa("b", Force.BLUE, mef=0.8)
    responses = [_coa(f"r{i}", Force.RED, mef=v) for i, v in enumerate([0.3, 0.5, 0.2])]
    assert robustness_score(coa, responses) == pytest.approx(0.2)


def test_robustness_score_no_adversaries():
    coa = _coa("b", Force.BLUE, mef=0.7)
    assert robustness_score(coa, []) == pytest.approx(0.7)


def test_coa_diversity_identical_actions():
    actions = [{"type": "advance"}]
    coas = [_coa(f"c{i}", Force.BLUE, actions=actions) for i in range(3)]
    # All identical => diversity == 0
    assert coa_diversity(coas) == pytest.approx(0.0)


def test_coa_diversity_disjoint_actions():
    coa1 = _coa("c1", Force.BLUE, actions=[{"type": "advance"}])
    coa2 = _coa("c2", Force.BLUE, actions=[{"type": "retreat"}])
    # Completely disjoint => diversity == 1
    assert coa_diversity([coa1, coa2]) == pytest.approx(1.0)


def test_coa_diversity_single_coa():
    coa = _coa("c1", Force.BLUE)
    assert coa_diversity([coa]) == 0.0
