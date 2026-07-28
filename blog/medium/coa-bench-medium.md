---
title: "A Plan Is Only Good If It Survives an Opponent"
subtitle: "COA-Bench studies course-of-action generation as an adversarial multi-agent evaluation problem."
original: "../coa-bench-self-play.md"
venue: "Medium draft"
date: "2026-07-28"
---

# A Plan Is Only Good If It Survives an Opponent

Course-of-action generation is not a normal planning problem.

A plan is not strong just because it looks coherent in isolation. It has to
survive an opponent.

That is the central idea behind our COA paper: treat course-of-action
generation as an adversarial, multi-agent evaluation problem.

A BLUE-side policy proposes structured courses of action. A RED-side policy
searches for plausible responses. A council of role-specialized agents can
propose, critique, revise, and select among alternatives.

The result is a small, inspectable benchmark for studying how generated plans
behave under adversarial pressure.

The paper is titled **Adversarial Course-of-Action Generation:
Game-Theoretic Multi-Agent Algorithms for COA Matching & COA Generation**.
The work frames COA generation as a game-theoretic agent interaction, then
implements a reproducible offline harness to test that framing.

## The Core Question

The paper asks:

> When a course-of-action generator is evaluated against a stronger adversarial
> response policy, do its apparent quality and robustness conclusions change?

COA-Bench represents each course of action as a typed structure, not only a
paragraph of prose. A COA includes an objective, ordered actions, targets,
priorities, optional tool calls, conditional branches, force assignments, and
domain tags.

That structure lets the benchmark compare policies on more than one score.

The benchmark uses synthetic scenarios only. It is not an operational planning
system, does not use real intelligence data, and does not claim tactical
validity. Its job is narrower: make adversarial COA evaluation reproducible,
inspectable, and falsifiable.

## COA-Bench as a Small Game

Each scenario is treated as a small game between BLUE and RED.

BLUE proposes a course of action. RED responds. The benchmark scores the pair
using a synthetic BLUE advantage signal, a Nash-gap-style distance from
balance, a doctrine-inspired diagnostic score, candidate diversity, and a
stylized wargame check.

The key comparison is between:

1. A single-sample RED response
2. A sampled best-response policy that draws multiple RED candidates and keeps
   the strongest
3. A doctrine-aware RED selector that trades some synthetic quality for
   stronger doctrinal alignment
4. A two-stage multi-agent BLUE council that proposes, stress-tests, revises,
   and adjudicates candidate COAs

This makes adversarial response part of the evaluation object.

A generated COA is not judged only against a fixed answer key. It is judged
against a response distribution and an inspectable candidate frontier.

## Why Use a Multi-Agent Council?

The council is the most title-aligned part of the work.

Instead of asking one generator for one plan, the council uses five
role-specialized BLUE proposer agents:

- Maneuver
- Intelligence
- Cyber
- Sustainment
- Protection

Each proposer creates a candidate COA with a different emphasis. RED-team
agents then generate adversarial responses to each candidate. An adjudicator
shortlists the strongest BLUE options, and a revision step adds mitigation
actions keyed to the strongest RED critique.

This creates a richer object than simple self-play.

The benchmark can measure proposal diversity, revised-candidate diversity,
adversarial pressure, consensus gap, robustness margin, pressure reduction, and
whether the selected final COA came from the revised set.

That matters because useful planning is often about surfacing a set of viable
options, not producing one polished paragraph.

## What Changed in the Results

The expanded experiment runs across **50 synthetic scenarios** spanning five
operational templates:

- Urban stability
- Maritime interdiction
- Multi-domain combat
- Suppression of enemy air defenses
- Humanitarian evacuation

The main result is that adversarial response search changes the evaluation.

With a single RED response, BLUE advantage is **0.516** and BLUE wargame win
rate is **0.920**.

When RED samples eight candidates and keeps the strongest response, BLUE
advantage falls to **0.485** and BLUE win rate falls to **0.820**.

That is the point.

A plan that looks strong against one response can look weaker once the opponent
is allowed to search.

The response-budget curve reinforces the same pattern. As RED samples more
candidates, BLUE advantage declines from **0.516** at one candidate to
**0.479** at sixteen candidates.

More adversarial search produces a tougher evaluation.

## Candidate Frontiers Are More Useful Than Single Scores

The sampled candidates are not redundant copies.

Across RED candidate sets, mean action-type diversity is **0.682**, mean
quality-score spread is **0.246**, and an average of **2.16 out of 8**
candidates are Pareto-optimal on the quality and doctrinal-alignment frontier.

That frontier matters.

In real planning workflows, the useful output is often not "the answer" but a
ranked set of alternatives with different tradeoffs.

COA-Bench makes those tradeoffs visible.

The doctrine-aware selector changes the chosen response in **56%** of
scenarios. It gives up **0.041** synthetic quality on average while gaining
**0.106** doctrinal alignment.

That result is useful because it shows the benchmark can distinguish
adversarial strength from doctrinal coherence rather than collapsing everything
into one number.

## What the Council Adds

The multi-agent council changes BLUE generation itself.

Across 50 scenarios, the council obtains **0.509** BLUE advantage and **0.820**
BLUE win rate. It partially recovers performance lost under stronger RED
response search.

The selected final COA comes from the revised set in **76%** of scenarios,
which suggests that critique-driven revision is doing real work in the current
synthetic setup.

The council also increases revised-candidate diversity to **0.644** and
produces a positive robustness margin of **0.014**.

Pressure reduction is small and uncertain, so the paper treats the council as a
repair-and-selection baseline, not a finished robust-optimization algorithm.

That distinction matters. The contribution is not "the system solved
planning." The contribution is an algorithmic scaffold for measuring how
proposal, red-teaming, revision, and adjudication interact.

## A Benchmark Bug Worth Reporting

One of the most useful findings was not a better score. It was a benchmark
design bug.

The scenario generator had a `framing` parameter intended to mark whether a
scenario was favorable to BLUE, neutral, or favorable to the adversary.

But that parameter was only stored as metadata. It did not affect objective
text or generated action content.

So the first framing-sensitivity test returned exactly zero.

The fix was deliberately small and inspectable: scenario framing now changes
generated objective text and can modify action composition. After that change,
framing sensitivity becomes **0.066** with a 95% bootstrap interval of
**[0.049, 0.086]**.

This is a good benchmark lesson:

> Evaluation variables must actually touch the generated artifact.

Otherwise, a benchmark can look configurable while measuring the same thing
every time.

## What This Work Does Not Claim

COA-Bench does not use classified data, proprietary data, human-subject data,
live planners, or deployed decision systems.

The wargame check is stylized. The doctrine rubric is heuristic. The scenarios
are synthetic. The current policies are programmatic baselines, not validated
military reasoning agents.

Those limitations are not footnotes. They are part of the research design.

Before moving to richer simulations or expert-scored environments, we need
small benchmarks where assumptions are visible and failures can be found.

## The Takeaway

Agentic planning systems need more than fluent outputs.

They need evaluations that ask what happens when another agent pushes back.

COA-Bench shows that stronger adversarial response search changes conclusions,
that candidate frontiers contain meaningful alternatives, that multi-agent
council revision can recover some robustness, and that benchmark variables can
silently fail if they are not wired into generated content.

That is the deeper message:

Course-of-action generation should be studied as a game between agents, not as
one-shot text generation.

