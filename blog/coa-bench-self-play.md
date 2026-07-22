---
title: "Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA Matching & COA Generation"
venue: "AAAI 2027"
status: "Completed"
date: "2026-07-16"
---

# Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA Matching & COA Generation

Course-of-action generation is not a normal planning problem. A plan is not strong just because it looks coherent in isolation. It has to survive an opponent.

That is the central idea behind our COA paper: treat course-of-action generation as an adversarial, multi-agent evaluation problem. A BLUE-side policy proposes structured COAs. A RED-side policy searches for plausible responses. A council of role-specialized agents can propose, critique, revise, and select among alternatives. The result is a small but inspectable benchmark for studying how generated plans behave under adversarial pressure.

The paper is titled **"Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA Matching & COA Generation."** The title is intentionally broader than a benchmark report: the work frames COA generation as a game-theoretic agent interaction, then implements a reproducible offline harness to test that framing.

## The Core Question

The paper asks a practical research question:

When a course-of-action generator is evaluated against a stronger adversarial response policy, do its apparent quality and robustness conclusions change?

To answer that, COA-Bench represents each COA as a typed structure rather than only prose. A COA includes an objective, ordered actions, targets, priorities, optional tool calls, conditional branches, force assignments, and domain tags. That structure lets the benchmark compare policies on more than one scalar score.

The benchmark uses synthetic scenarios only. It is not an operational battle-management system, does not use real intelligence data, and does not claim real-world tactical validity. Its job is narrower: make adversarial COA evaluation reproducible, inspectable, and falsifiable.

## Game-Theoretic Setup

COA-Bench treats each scenario as a small game between BLUE and RED.

BLUE proposes a course of action. RED responds. The benchmark scores the pair using a synthetic BLUE advantage signal, a Nash-gap-style distance from balance, a doctrine-inspired diagnostic score, candidate diversity, and a stylized wargame check.

The key algorithmic comparison is between:

1. A single-sample RED response
2. A sampled best-response policy that draws multiple RED candidates and keeps the strongest
3. A doctrine-aware RED selector that trades some synthetic quality for stronger doctrinal alignment
4. A two-stage multi-agent BLUE council that proposes, stress-tests, revises, and adjudicates candidate COAs

This makes adversarial response part of the evaluation object. A generated COA is not judged only against a fixed answer key; it is judged against a response distribution and an inspectable candidate frontier.

## Multi-Agent Council

The most title-aligned addition is the multi-agent council.

Instead of asking one generator for one plan, the council uses five role-specialized BLUE proposer agents: maneuver, intelligence, cyber, sustainment, and protection. Each proposer creates a candidate COA with a different operational emphasis. RED-team agents then generate adversarial responses to each candidate. An adjudicator shortlists the strongest BLUE options, and a revision step adds mitigation actions keyed to the strongest RED critique.

This gives the benchmark a richer technical object than simple self-play. It can measure:

- proposal diversity
- revised-candidate diversity
- adversarial pressure
- consensus gap
- robustness margin
- pressure reduction
- whether the selected final COA came from the revised set

That matters because useful COA generation is often about surfacing a set of viable options, not producing one polished paragraph.

## What Changed in the Results

The expanded experiment now runs across **50 synthetic scenarios** spanning five operational templates: urban stability, maritime interdiction, multi-domain combat, suppression of enemy air defenses, and humanitarian evacuation.

The main result is that adversarial response search changes the evaluation.

With a single RED response, BLUE advantage is **0.516** and BLUE wargame win rate is **0.920**. When RED samples eight candidates and keeps the strongest response, BLUE advantage falls to **0.485** and BLUE win rate falls to **0.820**.

That is the point: a plan that looks strong against one response can look weaker once the opponent is allowed to search.

The response-budget curve reinforces the same pattern. As RED samples more candidates, BLUE advantage declines from **0.516** at one candidate to **0.479** at sixteen candidates. More adversarial search produces a tougher evaluation.

## Candidate Frontiers

The sampled candidates are not redundant copies. Across RED candidate sets, mean action-type diversity is **0.682**, mean quality-score spread is **0.246**, and an average of **2.16 out of 8** candidates are Pareto-optimal on the quality and doctrinal-alignment frontier.

That frontier is important. In real planning workflows, the useful output is often not "the answer" but a ranked set of alternatives with different tradeoffs. COA-Bench makes those tradeoffs visible.

The doctrine-aware selector changes the chosen response in **56%** of scenarios. It gives up **0.041** synthetic quality on average while gaining **0.106** doctrinal alignment. That result is small but useful: it shows that the benchmark can distinguish adversarial strength from doctrinal coherence rather than collapsing everything into one number.

## Council Results

The multi-agent council changes BLUE generation itself. It does not merely make RED stronger.

Across 50 scenarios, the council obtains **0.509** BLUE advantage and **0.820** BLUE win rate. It partially recovers performance lost under stronger RED response search. The selected final COA comes from the revised set in **76%** of scenarios, which suggests that critique-driven revision is doing real work in the current synthetic setup.

The council also increases revised-candidate diversity to **0.644** and produces a positive robustness margin of **0.014**. Pressure reduction is small and uncertain, so the paper treats the council as a repair-and-selection baseline, not a finished robust-optimization algorithm.

That distinction is healthy. The contribution is not "the system solved military planning." The contribution is an algorithmic scaffold for measuring how proposal, red-teaming, revision, and adjudication interact.

## A Benchmark Bug Worth Reporting

One of the paper's most useful findings was not a better score. It was a benchmark-design bug.

The scenario generator had a `framing` parameter intended to mark whether a scenario was favorable to BLUE, neutral, or favorable to the adversary. But that parameter was only stored as metadata. It did not affect objective text or generated action content.

So the first framing-sensitivity test returned exactly zero.

The fix was deliberately small and inspectable: scenario framing now changes generated objective text and can modify action composition. After that change, framing sensitivity becomes **0.066** with a 95% bootstrap interval of **[0.049, 0.086]**.

This is a good benchmark lesson. Evaluation variables must actually touch the generated artifact. Otherwise, a benchmark can look configurable while measuring the same thing every time.

## Why the Work Is Novel

COA-Bench builds on familiar ideas: self-play, best-response search, agent evaluation, planning benchmarks, and doctrine-inspired diagnostics. The novelty is in putting them together around a structured adversarial COA artifact.

Compared with broad model benchmarks, COA-Bench is narrower but more traceable. Compared with tool-use benchmarks, it focuses less on whether an agent clicked the right tool and more on whether a structured plan survives adversarial response. Compared with self-refinement methods, it evaluates revision under explicit RED-team pressure rather than only final-answer polish.

The paper's technical contribution is the combination of:

- typed COA representation
- sampled adversarial best response
- doctrine-aware selection
- multi-agent proposal and critique
- candidate-frontier metrics
- robustness and pressure diagnostics
- reproducible trace artifacts

That combination gives researchers a concrete object for studying adversarial plan generation without pretending the synthetic benchmark is an operational planner.

## Scope Boundary

The paper is careful about what it does not claim.

COA-Bench does not use classified data, proprietary data, human-subject data, live planners, or deployed decision systems. The wargame check is stylized. The doctrine rubric is heuristic. The scenarios are synthetic. The current policies are programmatic baselines, not validated military reasoning agents.

Those limitations are not footnotes. They are part of the research design. Before moving to richer simulations or expert-scored environments, we need small benchmarks where assumptions are visible and failures can be found.

## Why It Matters

Agentic planning systems need more than fluent outputs. They need evaluations that ask what happens when another agent pushes back.

This paper contributes a first version of that evaluation for course-of-action generation. It shows that stronger adversarial response search changes conclusions, that candidate frontiers contain meaningful alternatives, that multi-agent council revision can recover some robustness, and that benchmark variables can silently fail if they are not wired into generated content.

That is the deeper message of the title: adversarial COA generation should be studied as a game between agents, not as one-shot text generation.

## Next Steps

The next version should expand the scenario corpus, validate the doctrine-inspired rubric with experts, evaluate LLM-backed policies, and replace deterministic revision rules with richer learned or model-guided critique. Longer term, COA-Bench should connect more directly to graph-structured BattleCOA-style planning while preserving the same reproducibility discipline.

For now, the contribution is a clear starting point: a game-theoretic, multi-agent benchmark for adversarial COA generation that makes plan quality, opponent pressure, diversity, revision, and failure modes visible.
