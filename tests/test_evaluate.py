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
    BootstrapResult,
    CandidateScore,
    CoaComparison,
    action_diversity_score,
    bootstrap_ci,
    bootstrap_ci_coa_diversity,
    bootstrap_ci_doctrinal_alignment,
    bootstrap_ci_gbc,
    bootstrap_ci_nash_gap,
    chain_coverage_score,
    coa_diversity,
    compare_coas,
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
from coageneration.core import Force, SampledBestResponsePolicy, SelfPlayEngine


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


def test_framing_sensitivity_delta_nonzero_for_urban_case() -> None:
    from coageneration.data import make_urban_operations_case

    scores = {
        framing: doctrinal_alignment_score(
            make_urban_operations_case(seed=10, framing=framing).seed_coas[0]
        )
        for framing in ("blue", "neutral", "adversary")
    }
    assert framing_sensitivity_delta(scores) > 0.0


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


# ---------------------------------------------------------------------------
# bootstrap_ci — core function
# ---------------------------------------------------------------------------


def test_bootstrap_ci_returns_bootstrap_result() -> None:
    coas = [make_coa(seed=i) for i in range(10)]
    result = bootstrap_ci(coa_diversity, coas, n_boot=200, seed=0)
    assert isinstance(result, BootstrapResult)


def test_bootstrap_ci_bounds_ordered() -> None:
    coas = [make_coa(seed=i) for i in range(10)]
    result = bootstrap_ci(coa_diversity, coas, n_boot=500, seed=1)
    assert result.lower <= result.mean <= result.upper


def test_bootstrap_ci_in_valid_range() -> None:
    coas = [make_coa(seed=i) for i in range(8)]
    result = bootstrap_ci(coa_diversity, coas, n_boot=300, seed=2)
    assert 0.0 <= result.lower
    assert result.upper <= 1.0


def test_bootstrap_ci_reproducible() -> None:
    coas = [make_coa(seed=i) for i in range(6)]
    r1 = bootstrap_ci(coa_diversity, coas, n_boot=200, seed=42)
    r2 = bootstrap_ci(coa_diversity, coas, n_boot=200, seed=42)
    assert r1.mean == r2.mean
    assert r1.lower == r2.lower
    assert r1.upper == r2.upper


def test_bootstrap_ci_wider_at_higher_confidence() -> None:
    coas = [make_coa(seed=i) for i in range(12)]
    r95 = bootstrap_ci(coa_diversity, coas, n_boot=500, confidence=0.95, seed=5)
    r80 = bootstrap_ci(coa_diversity, coas, n_boot=500, confidence=0.80, seed=5)
    assert (r95.upper - r95.lower) >= (r80.upper - r80.lower)


def test_bootstrap_ci_empty_data_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        bootstrap_ci(coa_diversity, [], n_boot=100)


def test_bootstrap_ci_bad_confidence_raises() -> None:
    coas = [make_coa(seed=0)]
    with pytest.raises(ValueError):
        bootstrap_ci(coa_diversity, coas, confidence=1.5)


def test_bootstrap_ci_str_representation() -> None:
    coas = [make_coa(seed=i) for i in range(6)]
    result = bootstrap_ci(coa_diversity, coas, n_boot=100, seed=0)
    s = str(result)
    assert "95% CI" in s
    assert "–" in s


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def test_bootstrap_ci_doctrinal_alignment_range() -> None:
    coas = [make_coa(seed=i) for i in range(10)]
    result = bootstrap_ci_doctrinal_alignment(coas, n_boot=300, seed=0)
    assert 0.0 <= result.lower <= result.upper <= 1.0


def test_bootstrap_ci_gbc_range() -> None:
    pairs = [(make_coa(force=Force.BLUE, seed=i), make_coa(force=Force.RED, seed=i + 50))
             for i in range(8)]
    result = bootstrap_ci_gbc(pairs, n_boot=300, seed=0)
    assert 0.0 <= result.lower <= result.upper <= 1.0


def test_bootstrap_ci_coa_diversity_single_element() -> None:
    coas = [make_coa(seed=0)]
    result = bootstrap_ci_coa_diversity(coas, n_boot=100, seed=0)
    assert result.lower == result.upper == result.mean == 0.0


def test_bootstrap_ci_nash_gap_at_equilibrium() -> None:
    pairs = [(0.6, 0.4)] * 20
    result = bootstrap_ci_nash_gap(pairs, n_boot=200, seed=0)
    assert result.mean == pytest.approx(0.0, abs=1e-9)
    assert result.lower == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# compare_coas
# ---------------------------------------------------------------------------


def test_compare_coas_returns_comparison() -> None:
    coas = [make_coa(seed=i) for i in range(4)]
    result = compare_coas(coas)
    assert isinstance(result, CoaComparison)
    assert len(result.scores) == 4
    assert all(isinstance(s, CandidateScore) for s in result.scores)


def test_compare_coas_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        compare_coas([])


def test_compare_coas_single_candidate() -> None:
    coa = make_coa(seed=0)
    result = compare_coas([coa])
    assert result.best.coa_id == coa.coa_id
    assert result.diversity == 0.0
    assert result.mef_spread == 0.0
    assert result.pareto_optimal_ids == [coa.coa_id]


def test_compare_coas_best_has_rank_one() -> None:
    coas = [make_coa(seed=i) for i in range(5)]
    result = compare_coas(coas)
    best_score = next(s for s in result.scores if s.coa_id == result.best.coa_id)
    assert best_score.rank == 1
    assert result.best.mef_score == max(c.mef_score for c in coas)


def test_compare_coas_ranks_are_a_permutation() -> None:
    coas = [make_coa(seed=i) for i in range(6)]
    result = compare_coas(coas)
    ranks = sorted(s.rank for s in result.scores)
    assert ranks == list(range(1, 7))


def test_compare_coas_mef_spread_matches_range() -> None:
    coas = [make_coa(seed=i) for i in range(5)]
    result = compare_coas(coas)
    mef_values = [c.mef_score for c in coas]
    assert result.mef_spread == pytest.approx(max(mef_values) - min(mef_values))


def test_compare_coas_pareto_optimal_includes_best() -> None:
    coas = [make_coa(seed=i) for i in range(5)]
    result = compare_coas(coas)
    assert result.best.coa_id in result.pareto_optimal_ids


def test_compare_coas_pareto_optimal_nonempty() -> None:
    coas = [make_coa(seed=i) for i in range(8)]
    result = compare_coas(coas)
    assert 1 <= len(result.pareto_optimal_ids) <= len(coas)


def test_compare_coas_from_sampled_policy_candidates() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=1)
    blue_coa = make_coa(force=Force.BLUE, seed=1)
    policy = SampledBestResponsePolicy(n_samples=5, seed=2)
    candidates = policy.generate_candidates(state, blue_coa)
    result = compare_coas(candidates)
    assert len(result.candidates) == 5
    assert result.best.force == Force.RED
