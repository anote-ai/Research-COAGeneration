---
title: "COA-Bench: A Small Reproducible Testbed for Course-of-Action Generation"
venue: "AAAI 2027"
status: "Completed"
date: "2026-07-16"
---

# Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA matching & COA generation

Course-of-action generation is a planning problem with a built-in adversary. A proposed plan is not good in isolation. It has to hold up against a response, fit the available force, preserve doctrinal coherence, and remain useful when the situation changes.

Our COA-Bench paper draft studies that problem in a small, fully offline setting. The goal is not to claim operational realism. The goal is to build a reproducible harness where we can compare course-of-action generation policies, inspect their tradeoffs, and find methodological problems before moving to richer simulations or live tools.

The current paper is titled **"COA-Bench: A Reproducible Self-Play Benchmark for Comparing Course-of-Action Generation Policies."**

## First, a Terminology Correction

The BattleCOA Boot Camp material uses two important acronyms:

- **MEF** means **Match Effectors**.
- **GBC** means **Generate BattleCOA**.

That matters because earlier internal drafts used those acronyms incorrectly for scalar scores. We corrected the paper and repository language so the benchmark now reserves MEF and GBC for the BattleCOA meanings.

In this draft, the scalar score assigned to a generated COA is called a **synthetic COA quality score**. The pairwise BLUE-vs-RED metric is called a **BLUE advantage score**. Some legacy code fields still use names like `mef_score` and `gbc_score` for compatibility, but the paper no longer presents those as BattleCOA definitions.

This correction is more than cosmetic. In a defense or battle-management context, acronym drift can make a research artifact look like it implements a formal decision function when it only implements a simplified metric. The paper now draws that boundary clearly.

## What COA-Bench Is Testing

The benchmark asks a narrow question:

Does sampling several candidate adversarial responses and keeping the strongest one change the evaluation of a generated course of action?

The setup is intentionally simple. For each scenario, we generate a fixed BLUE COA and compare two RED response policies:

1. A single-sample best response
2. A sampled best response that draws eight candidate responses and keeps the highest-quality one

The experiment runs on 30 synthetic scenarios:

- 10 random seeds
- 3 operational templates per seed
- Urban stability operations
- Maritime interdiction
- Multi-domain combat

Each COA is represented as a typed action structure: actions, targets, priorities, optional tool calls, conditional branches, force assignment, domain tags, and an objective string. This is not a natural-language-only benchmark. The representation is structured enough to support scoring, comparison, and future tool or LLM-backed generation.

## The Metrics

COA-Bench reports several metrics rather than relying on a single score.

The **synthetic quality score** combines effectiveness, cost, and risk into a scalar in `[-1, 1]`. This is a benchmark metric, not Match Effectors.

The **BLUE advantage score** compares a BLUE COA against a RED COA by measuring relative synthetic quality. A lower BLUE advantage score means RED has become a stronger opponent in that pairing.

The **Nash-gap distance** measures how far the pair is from a balanced zero-sum exchange after converting scores into payoffs.

The **doctrinal alignment score** is a heuristic rubric inspired by FM 3-0-style planning criteria: objective clarity, intelligence preparation, combined-arms balance, sustainment, risk mitigation, and tempo or sequencing.

The **wargame check** runs a stylized Lanchester-style attrition simulation where COA quality and doctrinal alignment affect effective combat power.

None of these metrics is treated as ground truth. The paper is explicit that the rubric is heuristic and unvalidated. That honesty is part of the contribution.

## Main Result

The sampled best-response policy makes RED a tougher opponent.

Across 30 scenarios:

- BLUE advantage score falls from **0.521** to **0.488**
- Nash gap rises from **0.194** to **0.259**
- RED doctrinal alignment improves from **0.651** to **0.671**
- BLUE wargame win rate falls from **0.967** to **0.833**

The interpretation is straightforward: when RED samples eight candidate responses and keeps the strongest one, RED becomes more competitive. BLUE's advantage falls, and the wargame check confirms the same direction of effect.

An interesting detail is that RED's doctrinal alignment also improves. In this generator, choosing the highest-quality response did not reduce doctrinal coherence. That is not a general claim about military planning. It is a narrow result about this synthetic action space and this heuristic rubric.

## Multi-COA Comparison

The paper also looks at the eight sampled RED candidates before the best one is selected.

Those candidates are not all redundant. The mean candidate diversity is **0.734**, and the mean quality-score spread is **0.242**. On average, about **2.20 of 8 candidates** are Pareto-optimal on the quality and doctrinal-alignment frontier.

That matters because a human planner may not want a single auto-selected COA. In many planning settings, the useful artifact is a set of meaningfully different options with different tradeoffs. COA-Bench can surface that frontier instead of collapsing everything into one answer too early.

## A Useful Methodological Bug

One of the most important findings was not a performance result. It was a bug in the benchmark design.

The scenario generator had a `framing` parameter, intended to represent whether the scenario was framed as favorable to BLUE, neutral, or favorable to the adversary. But the parameter was only stored as metadata. It did not affect the generated COA objective text or action content.

That meant a naive framing-sensitivity experiment produced exactly zero change. The problem was not that framing had no effect. The problem was that framing had never been wired into generation.

The paper fixes that in a minimal, inspectable way:

- Framing now changes the generated objective text.
- BLUE-favorable framing can add an action category that broadens combined-arms balance.

After the fix, framing sensitivity becomes **0.045**. The confidence interval is zero-width because the current manipulation is deterministic. The paper reports that honestly rather than pretending it is a rich stochastic effect.

This is the kind of result benchmarks need more often: not just "our method scored higher," but "our evaluation harness had a silent no-op, and here is how we found it."

## What COA-Bench Does Not Claim

COA-Bench is not an operational battle-management system.

It does not use real intelligence data, live planners, classified data, human-subject data, or deployed decision systems. The scenarios are synthetic. The wargame check is stylized. The doctrinal rubric is heuristic. The current evaluated policies are random-sampling policies, not a full LLM planning agent.

The paper should be read as a methods contribution and an early falsifiable experiment, not as evidence that the system can generate real-world military plans.

That boundary is especially important because BattleCOA terminology points toward a much richer decision architecture. Match Effectors and Generate BattleCOA are formal decision functions in that framing. COA-Bench currently implements a simplified research harness around typed COAs, self-play, and offline scoring.

## Why It Matters

The value of COA-Bench is that it gives us a place to ask disciplined questions about AI-assisted COA generation:

- Does self-play produce stronger adversarial responses?
- Do generated candidates actually differ from each other?
- Does selecting for quality destroy doctrinal coherence?
- Can a scenario-framing variable affect generated content?
- Which evaluation metrics move together, and which disagree?
- Where are the benchmark assumptions too brittle?

Those are the kinds of questions we need before claiming progress on more realistic agentic planning.

## Next Steps

The next version should expand the scenario corpus, replace deterministic framing rules with richer sampled generation, validate the doctrinal rubric with experts, and evaluate the LLM-backed policy already present in the repository.

Longer term, COA-Bench should connect more directly to the BattleCOA framing: Match Effectors should produce ranked EffectEffectorMatches, and Generate BattleCOA should build structured BattleCOA graphs from those matches. The current work is a smaller stepping stone: a reproducible self-play harness that makes policy comparison and benchmark failure modes visible.

That is a humble but useful place to start.

