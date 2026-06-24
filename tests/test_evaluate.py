"""Tests for coageneration evaluate."""

from __future__ import annotations

from coageneration.data import (
    make_coa,
    make_coa_with_branch,
    make_cyber_ops_coa,
    make_game_state,
    make_logistics_coa,
)
from coageneration.evaluate import (
    action_diversity_score,
    chain_coverage_score,
    coa_diversity,
    doctrinal_alignment_score,
    episode_summary,
    fm30_rubric_scores,
    framing_sensitivity_delta,
    gbc_score,
    lanchester_wargame_outcome,
    nash_gap,
    robustness_score,
    rubric_inter_rater_agreement,
    tool_utilisation_rate,
)
from coageneration.core import Force, SelfPlayEngine


def test_gbc_score_range() -> None:
    blue = make_coa(force=Force.BLUE, seed=1)
    red = make_coa(force=Force.RED, seed=2)
    score = gbc_score(blue, red)
    assert 0.0 <= score <= 1.0


def test_nash_gap_zero_sum() -> None:
    # At equilibrium blue + red payoffs should sum to 1
    assert nash_gap(0.6, 0.4) == pytest.approx(0.0, abs=1e-9)


def test_robustness_score_no_responses() -> None:
    coa = make_coa(seed=5)
    score = robustness_score(coa, [])
    assert score == coa.mef_score


def test_coa_diversity_identical_coas() -> None:
    coa = make_coa(seed=10)
    score = coa_diversity([coa, coa])
    assert score == 0.0


def test_coa_diversity_different_coas() -> None:
    coas = [make_coa(seed=i) for i in range(4)]
    score = coa_diversity(coas)
    assert 0.0 <= score <= 1.0


def test_chain_coverage_score_all_chained() -> None:
    coas = [make_coa(n_actions=3, with_chain=True) for _ in range(4)]
    score = chain_coverage_score(coas)
    assert score == 1.0


def test_chain_coverage_score_none_chained() -> None:
    coas = [make_coa(n_actions=3, with_chain=False) for _ in range(4)]
    score = chain_coverage_score(coas)
    assert score == 0.0


def test_chain_coverage_score_with_branch() -> None:
    coas = [make_coa_with_branch(seed=i) for i in range(3)]
    score = chain_coverage_score(coas)
    assert score == 1.0


def test_action_diversity_score_range() -> None:
    coas = [make_coa(seed=i, n_actions=5) for i in range(6)]
    score = action_diversity_score(coas)
    assert 0.0 <= score <= 1.0


def test_action_diversity_score_empty() -> None:
    assert action_diversity_score([]) == 0.0


def test_tool_utilisation_rate_cyber() -> None:
    coa = make_cyber_ops_coa()
    rate = tool_utilisation_rate([coa])
    assert rate == 1.0  # all cyber actions carry tool calls


def test_tool_utilisation_rate_no_tools() -> None:
    coas = [make_coa(n_actions=3, with_chain=False, seed=i) for i in range(3)]
    # Basic make_coa does not attach tool calls
    rate = tool_utilisation_rate(coas)
    assert rate == 0.0


def test_fm30_rubric_scores_range() -> None:
    coa = make_logistics_coa()
    scores = fm30_rubric_scores(coa)
    assert "sustainment" in scores
    assert all(0.0 <= score <= 1.0 for score in scores.values())


def test_doctrinal_alignment_score_range() -> None:
    coa = make_coa_with_branch(objective="protect civilians while isolating threat")
    score = doctrinal_alignment_score(coa)
    assert 0.0 <= score <= 1.0


def test_rubric_inter_rater_agreement_identical() -> None:
    ratings = [
        {"objective_clarity": 0.8, "sustainment": 0.4},
        {"objective_clarity": 0.8, "sustainment": 0.4},
    ]
    assert rubric_inter_rater_agreement(ratings) == pytest.approx(1.0)


def test_framing_sensitivity_delta() -> None:
    delta = framing_sensitivity_delta({"blue": 0.8, "neutral": 0.7, "adversary": 0.55})
    assert delta == pytest.approx(0.25)


def test_lanchester_wargame_outcome_shape() -> None:
    state = make_game_state()
    blue = make_logistics_coa(force=Force.BLUE)
    red = make_coa(force=Force.RED, seed=88)
    outcome = lanchester_wargame_outcome(state, blue, red, steps=3)
    assert outcome["winner"] in {"blue", "red", "draw"}
    assert outcome["blue_remaining"] >= 0.0
    assert outcome["red_remaining"] >= 0.0


def test_episode_summary_winner() -> None:
    state = make_game_state()
    engine = SelfPlayEngine(seed=99)
    states = engine.run_episode(state, n_rounds=3)
    summary = episode_summary(states)
    assert summary["winner"] in {"blue", "red", "draw"}
    assert summary["n_rounds"] == 3


import pytest  # noqa: E402  (kept at bottom to avoid circular import concerns)
