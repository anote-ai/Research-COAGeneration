"""Tests for coageneration.evaluate."""

import pytest
from coageneration.core import Action, Asset, CourseOfAction, Force, GameState
from coageneration.evaluate import (
    coa_diversity,
    episode_summary,
    gbc_score,
    nash_gap,
    robustness_score,
)


def _coa(force=Force.BLUE, mef=0.5, action_types=None):
    if action_types is None:
        action_types = ["attack"]
    actions = [
        Action(action_type=at, asset_id="a1") for at in action_types
    ]
    return CourseOfAction(force=force, actions=actions, objective="test", mef_score=mef)


def _state(blue_cap=0.8, red_cap=0.6, n_blue=1, n_red=1):
    blue = [
        Asset(asset_id=f"b{i}", asset_type="inf", force=Force.BLUE,
              location=(0.0, 0.0), capability_score=blue_cap)
        for i in range(n_blue)
    ]
    red = [
        Asset(asset_id=f"r{i}", asset_type="inf", force=Force.RED,
              location=(0.0, 0.0), capability_score=red_cap)
        for i in range(n_red)
    ]
    return GameState(blue_assets=blue, red_assets=red)


def test_gbc_score_in_range():
    blue = _coa(mef=0.8)
    red = _coa(force=Force.RED, mef=0.3)
    score = gbc_score(blue, red)
    assert 0.0 <= score <= 1.0


def test_nash_gap_zero_sum():
    # blue=0.6, red=0.4 → sum=1.0 → gap=0
    gap = nash_gap(0.6, 0.4)
    assert gap == pytest.approx(0.0)


def test_robustness_score_empty_adversaries():
    coa = _coa(mef=0.7)
    assert robustness_score(coa, []) == pytest.approx(0.7)


def test_robustness_score_min():
    coa = _coa(mef=0.7)
    adversaries = [_coa(mef=0.5), _coa(mef=0.2), _coa(mef=0.8)]
    assert robustness_score(coa, adversaries) == pytest.approx(0.2)


def test_coa_diversity_single_coa():
    coa = _coa(action_types=["attack", "defend"])
    assert coa_diversity([coa]) == pytest.approx(0.0)


def test_coa_diversity_distinct_coas():
    coa1 = _coa(action_types=["attack"])
    coa2 = _coa(action_types=["defend"])
    diversity = coa_diversity([coa1, coa2])
    assert diversity > 0.0


def test_episode_summary_structure():
    states = [_state(blue_cap=0.8, red_cap=0.6)] * 4
    summary = episode_summary(states)
    assert "n_rounds" in summary
    assert "final_blue_capability" in summary
    assert "final_red_capability" in summary
    assert "winner" in summary
    assert summary["winner"] in {"blue", "red", "draw"}
