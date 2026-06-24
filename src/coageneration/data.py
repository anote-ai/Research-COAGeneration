"""Factory helpers and domain templates for coageneration."""

from __future__ import annotations

import random
from typing import List

from .core import (
    Action,
    ActionCategory,
    Asset,
    ChainStep,
    ConditionalBranch,
    CourseOfAction,
    Force,
    GameState,
    ScenarioCase,
    ScenarioProfile,
    ToolCall,
    build_chain,
    compute_mef_score,
)


def make_asset(
    force: Force = Force.BLUE,
    capability: float = 0.8,
    asset_id: str = "asset-001",
    asset_type: str = "infantry",
    location: tuple = (10.0, 20.0),
) -> Asset:
    return Asset(
        asset_id=asset_id,
        asset_type=asset_type,
        force=force,
        location=location,
        capability_score=capability,
    )


def make_action(
    asset_id: str = "a1",
    action_type: str = "attack",
    target_location: tuple = (50.0, 50.0),
    priority: int = 1,
    category: ActionCategory = ActionCategory.KINETIC,
    tool_name: str | None = None,
) -> Action:
    tool_call = (
        ToolCall(tool_name=tool_name, arguments={"asset_id": asset_id})
        if tool_name is not None
        else None
    )
    return Action(
        action_type=action_type,
        category=category,
        target_location=target_location,
        asset_id=asset_id,
        priority=priority,
        tool_call=tool_call,
    )


def make_coa(
    force: Force = Force.BLUE,
    n_actions: int = 3,
    objective: str = "neutralize red",
    seed: int = 42,
    domain: str = "military",
    with_chain: bool = True,
) -> CourseOfAction:
    rng = random.Random(seed)
    action_types = ["attack", "defend", "maneuver", "recon", "support", "jam", "spoof"]
    categories = list(ActionCategory)
    actions = [
        Action(
            action_type=rng.choice(action_types),
            category=rng.choice(categories),
            target_location=(rng.uniform(0, 100), rng.uniform(0, 100)),
            asset_id=f"asset-{i:03d}",
            priority=rng.randint(1, 10),
            expected_duration_s=rng.uniform(30, 600),
        )
        for i in range(n_actions)
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.5, 1.0),
        cost=rng.uniform(0.1, 0.5),
        risk=rng.uniform(0.05, 0.3),
    )
    chain = build_chain(actions) if with_chain else []
    return CourseOfAction(
        force=force,
        actions=actions,
        chain=chain,
        objective=objective,
        mef_score=mef,
        domain=domain,
    )


def make_coa_with_branch(
    force: Force = Force.BLUE,
    objective: str = "conditional strike",
    seed: int = 0,
) -> CourseOfAction:
    """Build a COA that includes a conditional branch step."""
    rng = random.Random(seed)
    primary = Action(
        action_type="recon",
        category=ActionCategory.INTELLIGENCE,
        asset_id="isr-001",
        priority=1,
        expected_duration_s=120.0,
    )
    true_action = Action(
        action_type="strike",
        category=ActionCategory.KINETIC,
        asset_id="strike-001",
        priority=2,
        target_location=(rng.uniform(0, 100), rng.uniform(0, 100)),
        tool_call=ToolCall(
            tool_name="fire_control",
            arguments={"warhead": "precision", "yield_kg": 50},
            expected_output_type="strike_result",
        ),
    )
    false_action = Action(
        action_type="withdraw",
        category=ActionCategory.LOGISTICS,
        asset_id="strike-001",
        priority=2,
    )
    branch = ConditionalBranch(
        condition="target_confirmed",
        true_actions=[true_action],
        false_actions=[false_action],
    )
    step0 = ChainStep(step_index=0, action=primary, depends_on=[])
    step1 = ChainStep(step_index=1, branch=branch, depends_on=[0])
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.5, 0.9),
        cost=rng.uniform(0.1, 0.4),
        risk=rng.uniform(0.05, 0.3),
    )
    return CourseOfAction(
        force=force,
        actions=[primary],
        chain=[step0, step1],
        objective=objective,
        mef_score=mef,
        domain="military",
    )


# ---------------------------------------------------------------------------
# Domain-specific COA templates
# ---------------------------------------------------------------------------


def make_cyber_ops_coa(force: Force = Force.BLUE, seed: int = 1) -> CourseOfAction:
    """Cyber operations COA: recon → exploit → exfiltrate."""
    rng = random.Random(seed)
    actions = [
        Action(
            action_type="network_scan",
            category=ActionCategory.CYBER,
            asset_id="cyber-agent-001",
            priority=1,
            tool_call=ToolCall(
                tool_name="nmap",
                arguments={"target_subnet": "10.0.0.0/24", "ports": "1-1024"},
                expected_output_type="host_list",
            ),
            expected_duration_s=30.0,
        ),
        Action(
            action_type="exploit_vuln",
            category=ActionCategory.CYBER,
            asset_id="cyber-agent-001",
            priority=2,
            preconditions=["network_scan_complete"],
            tool_call=ToolCall(
                tool_name="metasploit",
                arguments={"module": "ms17_010_eternalblue"},
                expected_output_type="shell_session",
            ),
            expected_duration_s=60.0,
        ),
        Action(
            action_type="exfiltrate_data",
            category=ActionCategory.CYBER,
            asset_id="cyber-agent-001",
            priority=3,
            preconditions=["shell_obtained"],
            tool_call=ToolCall(
                tool_name="data_exfil",
                arguments={"target_files": ["/etc/shadow", "/var/log"], "encrypt": True},
                expected_output_type="exfil_bundle",
            ),
            expected_duration_s=90.0,
        ),
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.6, 0.95),
        cost=rng.uniform(0.05, 0.3),
        risk=rng.uniform(0.1, 0.5),
    )
    return CourseOfAction(
        force=force,
        actions=actions,
        chain=build_chain(actions),
        objective="achieve persistent access to adversary network",
        mef_score=mef,
        domain="cyber",
    )


def make_logistics_coa(force: Force = Force.BLUE, seed: int = 2) -> CourseOfAction:
    """Logistics / resupply COA: assess → transport → distribute."""
    rng = random.Random(seed)
    actions = [
        Action(
            action_type="assess_supply_levels",
            category=ActionCategory.LOGISTICS,
            asset_id="log-001",
            priority=1,
            tool_call=ToolCall(
                tool_name="inventory_query",
                arguments={"depot": "FOB-Alpha", "categories": ["ammo", "fuel", "med"]},
                expected_output_type="inventory_report",
            ),
            expected_duration_s=15.0,
        ),
        Action(
            action_type="convoy_dispatch",
            category=ActionCategory.LOGISTICS,
            asset_id="log-001",
            priority=2,
            target_location=(rng.uniform(20, 80), rng.uniform(20, 80)),
            preconditions=["route_cleared"],
            expected_duration_s=3600.0,
        ),
        Action(
            action_type="distribute_supplies",
            category=ActionCategory.LOGISTICS,
            asset_id="log-001",
            priority=3,
            preconditions=["convoy_arrived"],
            tool_call=ToolCall(
                tool_name="supply_allocation",
                arguments={"priority_units": ["bravo-co", "charlie-co"]},
                expected_output_type="allocation_receipt",
            ),
            expected_duration_s=1800.0,
        ),
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.5, 0.85),
        cost=rng.uniform(0.2, 0.5),
        risk=rng.uniform(0.05, 0.2),
    )
    return CourseOfAction(
        force=force,
        actions=actions,
        chain=build_chain(actions),
        objective="restore combat readiness through resupply",
        mef_score=mef,
        domain="logistics",
    )


def make_info_ops_coa(force: Force = Force.BLUE, seed: int = 3) -> CourseOfAction:
    """Information operations COA: analyse → craft → disseminate."""
    rng = random.Random(seed)
    actions = [
        Action(
            action_type="sentiment_analysis",
            category=ActionCategory.INFORMATION,
            asset_id="info-agent-001",
            priority=1,
            tool_call=ToolCall(
                tool_name="nlp_pipeline",
                arguments={"sources": ["twitter", "telegram"], "window_h": 24},
                expected_output_type="sentiment_report",
            ),
            expected_duration_s=300.0,
        ),
        Action(
            action_type="craft_narrative",
            category=ActionCategory.INFORMATION,
            asset_id="info-agent-001",
            priority=2,
            preconditions=["sentiment_analysis_complete"],
            tool_call=ToolCall(
                tool_name="content_generator",
                arguments={"tone": "authoritative", "language": "en", "length": 280},
                expected_output_type="narrative_draft",
            ),
            expected_duration_s=120.0,
        ),
        Action(
            action_type="disseminate",
            category=ActionCategory.INFORMATION,
            asset_id="info-agent-001",
            priority=3,
            preconditions=["narrative_approved"],
            tool_call=ToolCall(
                tool_name="broadcast",
                arguments={"channels": ["radio", "social"], "target_region": "sector-7"},
                expected_output_type="delivery_receipt",
            ),
            expected_duration_s=60.0,
        ),
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.4, 0.8),
        cost=rng.uniform(0.05, 0.25),
        risk=rng.uniform(0.1, 0.4),
    )
    return CourseOfAction(
        force=force,
        actions=actions,
        chain=build_chain(actions),
        objective="shape adversary population perception",
        mef_score=mef,
        domain="information_ops",
    )


def make_urban_operations_case(seed: int = 10, framing: str = "neutral") -> ScenarioCase:
    """Dense urban scenario with ISR, maneuver, logistics, and restraint needs."""
    state = make_game_state(n_blue=6, n_red=5, seed=seed)
    profile = ScenarioProfile(
        scenario_id=f"urban-{seed}",
        terrain_type="urban",
        force_size="company",
        operational_phase="stability",
        domains=["land", "cyber", "information"],
        framing=framing,
        loac_ambiguity="high",
        historical_reference="synthetic urban stability operation",
    )
    coas = [
        make_coa_with_branch(
            force=Force.BLUE,
            objective="isolate hostile element while protecting civilians",
            seed=seed,
        ),
        make_info_ops_coa(force=Force.BLUE, seed=seed + 1),
        make_logistics_coa(force=Force.BLUE, seed=seed + 2),
    ]
    return ScenarioCase(profile=profile, game_state=state, seed_coas=coas)


def make_maritime_operations_case(seed: int = 20, framing: str = "neutral") -> ScenarioCase:
    """Maritime interdiction scenario with surveillance and escalation control."""
    rng = random.Random(seed)
    blue_assets = [
        Asset(
            asset_id=f"blue-mar-{i:03d}",
            asset_type=["destroyer", "patrol_aircraft", "boarding_team"][i % 3],
            force=Force.BLUE,
            location=(rng.uniform(0, 40), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.55, 0.95),
        )
        for i in range(5)
    ]
    red_assets = [
        Asset(
            asset_id=f"red-mar-{i:03d}",
            asset_type=["fast_boat", "merchant_cover", "coastal_sensor"][i % 3],
            force=Force.RED,
            location=(rng.uniform(60, 100), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.45, 0.85),
        )
        for i in range(4)
    ]
    actions = [
        make_action(
            asset_id="blue-mar-001",
            action_type="maritime_surveillance",
            category=ActionCategory.INTELLIGENCE,
            priority=1,
            tool_name="ais_fusion",
        ),
        make_action(
            asset_id="blue-mar-000",
            action_type="hail_and_query",
            category=ActionCategory.INFORMATION,
            priority=2,
            tool_name="comms_log",
        ),
        make_action(
            asset_id="blue-mar-002",
            action_type="compliant_boarding",
            category=ActionCategory.KINETIC,
            priority=3,
        ),
    ]
    coa = CourseOfAction(
        force=Force.BLUE,
        actions=actions,
        chain=build_chain(actions),
        objective="interdict suspected smuggling vessel with minimum escalation",
        mef_score=compute_mef_score(0.72, 0.28, 0.22),
        domain="maritime",
    )
    profile = ScenarioProfile(
        scenario_id=f"maritime-{seed}",
        terrain_type="maritime",
        force_size="task_group",
        operational_phase="interdiction",
        domains=["maritime", "air", "information"],
        framing=framing,
        loac_ambiguity="medium",
        historical_reference="synthetic maritime interdiction",
    )
    return ScenarioCase(
        profile=profile,
        game_state=GameState(blue_assets=blue_assets, red_assets=red_assets),
        seed_coas=[coa],
    )


def make_multi_domain_operations_case(
    seed: int = 30, framing: str = "neutral"
) -> ScenarioCase:
    """Multi-domain scenario spanning land, cyber, information, and logistics."""
    state = make_game_state(n_blue=8, n_red=8, seed=seed)
    profile = ScenarioProfile(
        scenario_id=f"multi-domain-{seed}",
        terrain_type="mixed",
        force_size="battalion",
        operational_phase="large_scale_combat",
        domains=["land", "air", "cyber", "information", "logistics"],
        framing=framing,
        loac_ambiguity="medium",
        historical_reference="synthetic large-scale combat operation",
    )
    return ScenarioCase(
        profile=profile,
        game_state=state,
        seed_coas=[
            make_cyber_ops_coa(force=Force.BLUE, seed=seed),
            make_info_ops_coa(force=Force.BLUE, seed=seed + 1),
            make_logistics_coa(force=Force.BLUE, seed=seed + 2),
            make_coa(force=Force.BLUE, n_actions=5, seed=seed + 3),
        ],
    )


def make_scenario_corpus(seed: int = 100) -> List[ScenarioCase]:
    """Return a small, diverse corpus for benchmark smoke tests."""
    return [
        make_urban_operations_case(seed=seed, framing="blue"),
        make_maritime_operations_case(seed=seed + 1, framing="neutral"),
        make_multi_domain_operations_case(seed=seed + 2, framing="adversary"),
    ]


def make_game_state(
    n_blue: int = 5,
    n_red: int = 5,
    seed: int = 42,
) -> GameState:
    rng = random.Random(seed)
    blue_asset_types = ["infantry", "armor", "artillery", "air", "naval"]
    red_asset_types = ["infantry", "armor", "artillery", "air", "naval"]

    blue_assets = [
        Asset(
            asset_id=f"blue-{i:03d}",
            asset_type=blue_asset_types[i % len(blue_asset_types)],
            force=Force.BLUE,
            location=(rng.uniform(0, 50), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.5, 1.0),
        )
        for i in range(n_blue)
    ]
    red_assets = [
        Asset(
            asset_id=f"red-{i:03d}",
            asset_type=red_asset_types[i % len(red_asset_types)],
            force=Force.RED,
            location=(rng.uniform(50, 100), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.5, 1.0),
        )
        for i in range(n_red)
    ]
    return GameState(blue_assets=blue_assets, red_assets=red_assets, turn=0)
