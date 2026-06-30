"""Tests for coageneration core."""

from __future__ import annotations

import pytest

from coageneration.core import (
    Action,
    ActionCategory,
    Asset,
    ChainStep,
    ConditionalBranch,
    CourseOfAction,
    Force,
    GameState,
    SampledBestResponsePolicy,
    SelfPlayEngine,
    ToolCall,
    build_chain,
    compute_mef_score,
)
from coageneration.data import (
    make_asset,
    make_coa,
    make_coa_with_branch,
    make_cyber_ops_coa,
    make_game_state,
)


# ---------------------------------------------------------------------------
# compute_mef_score
# ---------------------------------------------------------------------------


def test_mef_score_clamped() -> None:
    score = compute_mef_score(effectiveness=1.0, cost=0.0, risk=0.0)
    assert score <= 1.0
    score = compute_mef_score(effectiveness=0.0, cost=1.0, risk=1.0)
    assert score >= -1.0


def test_mef_score_range() -> None:
    for e, c, r in [(0.5, 0.3, 0.2), (0.9, 0.1, 0.05), (0.2, 0.8, 0.5)]:
        s = compute_mef_score(e, c, r)
        assert -1.0 <= s <= 1.0


# ---------------------------------------------------------------------------
# ToolCall & Action
# ---------------------------------------------------------------------------


def test_action_with_tool_call() -> None:
    tc = ToolCall(
        tool_name="nmap",
        arguments={"target": "10.0.0.1"},
        expected_output_type="host_list",
    )
    action = Action(
        action_type="network_scan",
        asset_id="cyber-001",
        category=ActionCategory.CYBER,
        tool_call=tc,
    )
    assert action.tool_call is not None
    assert action.tool_call.tool_name == "nmap"


def test_action_priority_bounds() -> None:
    with pytest.raises(Exception):
        Action(action_type="x", asset_id="a", priority=0)  # must be >= 1
    with pytest.raises(Exception):
        Action(action_type="x", asset_id="a", priority=11)  # must be <= 10


# ---------------------------------------------------------------------------
# build_chain
# ---------------------------------------------------------------------------


def test_build_chain_linear_deps() -> None:
    actions = [
        Action(action_type=f"step{i}", asset_id="a")
        for i in range(4)
    ]
    chain = build_chain(actions, linear=True)
    assert len(chain) == 4
    assert chain[0].depends_on == []
    assert chain[1].depends_on == [0]
    assert chain[3].depends_on == [2]


def test_build_chain_parallel_no_deps() -> None:
    actions = [Action(action_type=f"p{i}", asset_id="a") for i in range(3)]
    chain = build_chain(actions, linear=False)
    assert all(step.depends_on == [] for step in chain)


# ---------------------------------------------------------------------------
# ConditionalBranch & ChainStep
# ---------------------------------------------------------------------------


def test_conditional_branch_in_coa() -> None:
    coa = make_coa_with_branch(force=Force.BLUE, seed=7)
    branch_steps = [s for s in coa.chain if s.branch is not None]
    assert len(branch_steps) >= 1
    b = branch_steps[0].branch
    assert b is not None
    assert len(b.true_actions) >= 1
    assert len(b.false_actions) >= 1


def test_coa_all_action_types_includes_branch() -> None:
    coa = make_coa_with_branch()
    types = coa.all_action_types()
    assert len(types) >= 2  # primary + at least one branch arm


# ---------------------------------------------------------------------------
# CourseOfAction
# ---------------------------------------------------------------------------


def test_make_coa_with_chain() -> None:
    coa = make_coa(n_actions=4, with_chain=True)
    assert len(coa.chain) == 4


def test_make_coa_without_chain() -> None:
    coa = make_coa(n_actions=3, with_chain=False)
    assert coa.chain == []


def test_coa_unique_tool_names() -> None:
    coa = make_cyber_ops_coa()
    tools = coa.unique_tool_names()
    assert len(tools) == len(set(tools))  # no duplicates
    assert len(tools) >= 2  # cyber ops uses multiple tools


# ---------------------------------------------------------------------------
# GameState & SelfPlayEngine
# ---------------------------------------------------------------------------


def test_game_state_capability_totals() -> None:
    state = make_game_state(n_blue=3, n_red=3)
    assert state.blue_capability_total() > 0
    assert state.red_capability_total() > 0


def test_self_play_engine_episode_length() -> None:
    state = make_game_state()
    engine = SelfPlayEngine(seed=0)
    states = engine.run_episode(state, n_rounds=3)
    assert len(states) == 4  # initial + 3 rounds


def test_self_play_engine_capability_monotone_decrease() -> None:
    state = make_game_state(n_blue=2, n_red=2)
    engine = SelfPlayEngine(seed=0)
    states = engine.run_episode(state, n_rounds=5)
    blue_caps = [s.blue_capability_total() for s in states]
    # Capabilities should be non-increasing overall (small noise means not strictly)
    assert blue_caps[-1] <= blue_caps[0] + 0.5


def test_best_response_opposite_force() -> None:
    state = make_game_state()
    engine = SelfPlayEngine(seed=42)
    blue_coa = make_coa(force=Force.BLUE)
    response = engine.best_response(blue_coa, state)
    assert response.force == Force.RED


# ---------------------------------------------------------------------------
# SampledBestResponsePolicy
# ---------------------------------------------------------------------------


def test_sampled_policy_returns_correct_force() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=0)
    blue_coa = make_coa(force=Force.BLUE, seed=0)
    policy = SampledBestResponsePolicy(n_samples=5, seed=1)
    result = policy.generate_coa(state, blue_coa)
    assert result.force == Force.RED


def test_sampled_policy_red_responds_as_blue() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=0)
    red_coa = make_coa(force=Force.RED, seed=0)
    policy = SampledBestResponsePolicy(n_samples=5, seed=2)
    result = policy.generate_coa(state, red_coa)
    assert result.force == Force.BLUE


def test_sampled_policy_picks_highest_mef() -> None:
    # With enough samples, sampled policy should consistently beat single-sample.
    state = make_game_state(n_blue=5, n_red=5, seed=7)
    blue_coa = make_coa(force=Force.BLUE, seed=7)

    single_scores = [
        SelfPlayEngine(seed=i).best_response(blue_coa, state).mef_score
        for i in range(20)
    ]
    policy = SampledBestResponsePolicy(n_samples=16, seed=99)
    sampled_score = policy.generate_coa(state, blue_coa).mef_score

    # Sampled policy should beat the average of single-sample attempts.
    assert sampled_score >= sum(single_scores) / len(single_scores)


def test_sampled_policy_chain_populated() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=3)
    blue_coa = make_coa(force=Force.BLUE, n_actions=3, seed=3)
    policy = SampledBestResponsePolicy(n_samples=4, seed=4)
    result = policy.generate_coa(state, blue_coa)
    assert len(result.chain) == len(result.actions)


def test_sampled_policy_n_samples_validation() -> None:
    with pytest.raises(ValueError):
        SampledBestResponsePolicy(n_samples=0)


def test_sampled_policy_reproducible_with_same_seed() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=5)
    blue_coa = make_coa(force=Force.BLUE, seed=5)
    p1 = SampledBestResponsePolicy(n_samples=6, seed=42)
    p2 = SampledBestResponsePolicy(n_samples=6, seed=42)
    r1 = p1.generate_coa(state, blue_coa)
    r2 = p2.generate_coa(state, blue_coa)
    assert r1.mef_score == r2.mef_score


def test_engine_with_sampled_policy_episode() -> None:
    state = make_game_state(n_blue=4, n_red=4, seed=6)
    policy = SampledBestResponsePolicy(n_samples=8, seed=6)
    engine = SelfPlayEngine(seed=6, policy=policy)
    states = engine.run_episode(state, n_rounds=4)
    assert len(states) == 5


def test_generate_candidates_returns_n_samples() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=0)
    blue_coa = make_coa(force=Force.BLUE, seed=0)
    policy = SampledBestResponsePolicy(n_samples=5, seed=1)
    candidates = policy.generate_candidates(state, blue_coa)
    assert len(candidates) == 5
    assert all(c.force == Force.RED for c in candidates)


def test_generate_candidates_best_matches_generate_coa() -> None:
    # generate_coa should pick the max-MEF candidate from the same stream
    # generate_candidates would produce for a freshly-seeded policy.
    state = make_game_state(n_blue=3, n_red=3, seed=2)
    blue_coa = make_coa(force=Force.BLUE, seed=2)
    policy = SampledBestResponsePolicy(n_samples=6, seed=3)
    candidates = policy.generate_candidates(state, blue_coa)
    best = max(candidates, key=lambda c: c.mef_score)

    policy2 = SampledBestResponsePolicy(n_samples=6, seed=3)
    result = policy2.generate_coa(state, blue_coa)
    assert result.mef_score == best.mef_score
