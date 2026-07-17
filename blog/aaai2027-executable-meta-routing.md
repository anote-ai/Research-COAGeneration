---
title: "Learning When an Agent Should Decompose, Retrieve, Code, Delegate, or Verify"
venue: "AAAI 2027"
status: "Completed"
date: "2026-07-07"
---

# Learning When an Agent Should Decompose, Retrieve, Code, Delegate, or Verify

Agentic AI systems are built from choices. Before producing an answer, the system may need to decompose the task, retrieve evidence, execute code, delegate to a specialist, verify a candidate result, or answer directly.

The research question behind our AAAI 2027 paper draft is: can we learn that routing policy from task text, and can we evaluate it with executable outcomes rather than sampled or subjective success?

Our paper, **"Learning Compositional Meta-Routing for Agentic Workflows: An Executable Benchmark,"** introduces a benchmark for testing the meta-decision layer of agentic systems. The focus is not on building a new foundation model. It is on deciding which operations should surround a model call.

## Why Meta-Routing?

Most routing work asks which model to use, how much retrieval to perform, or which tool should be called. Those are important questions, but agentic workflows often need a broader decision:

Should this task be answered directly, or should the system build a route?

A route might look like:

```text
decompose -> retrieve -> verify -> answer
```

or:

```text
retrieve -> code -> verify -> answer
```

or:

```text
delegate -> answer
```

The right route depends on the task. A direct literal question does not need a workflow. A multi-hop research task may need decomposition and retrieval. An invoice task may need extraction, computation, and verification. A retrieval outage may require delegation instead of the usual tool path.

The paper studies this operation-level routing problem directly.

## What Makes the Benchmark Executable

The AAAI benchmark contains 504 generated tasks:

- 216 training tasks
- 72 development tasks
- 108 held-out test tasks
- 108 locked lexical-shift challenge tasks

The tasks span three workloads:

- Data analysis
- Frozen-corpus research
- Document processing

Each task has an exact answer checker. Success is not sampled from a simulator and is not assigned because the route overlaps with labels. Operations execute deterministic local semantics and produce a candidate answer, which is then checked.

For example:

- A filtered-sum task requires decomposition before code; otherwise the system sums the wrong subset.
- A multi-hop research task requires decomposition plus retrieval; retrieval alone returns an intermediate entity.
- A conflicting-source task requires retrieval plus verification; otherwise the system may return stale evidence.
- A retrieval-outage task requires delegation because the usual retrieval path is unavailable.

This setup is intentionally small, but it gives us something valuable: machine-checked, reproducible outcomes for different routing policies.

## The Learned Router

The learned router receives only raw task text. It predicts probabilities for five support operations:

- Decomposition
- Retrieval/tool use
- Code execution
- Delegation
- Verification

The model uses independent regularized logistic heads over word unigrams, word bigrams, and character 3-5 grams. The heads are temperature-scaled on development data, and a threshold is selected on the development split.

At inference time, the router greedily composes operations under two constraints:

- At most three support operations
- A normalized route-cost budget

The final answer action is always appended. The result is a budget-aware route such as:

```text
decompose -> retrieve -> verify -> answer
```

The design is deliberately lightweight. It is not trying to win by using a large opaque controller. It is trying to isolate whether compositional routing helps when the policy is trained from text.

## Baselines

The paper compares the learned budget-aware router against several baselines:

- Direct answering
- Random routing
- Keyword rules
- Static workload routing
- A fixed agent that executes all support operations
- A learned one-shot router
- An oracle route

The learned one-shot router is especially important. It uses the same text representation and supervision as the compositional router, but it can select only one support operation. That comparison isolates the value of composing multiple operations.

## Main Results

On the held-out test split, the learned budget-aware router solves all 108 tasks:

- Learned budget router: **100% success**, cost **1.76**
- Static workload router: **93.5% success**, cost **3.08**
- Fixed agent: **93.5% success**, cost **4.95**
- Learned one-shot router: **56.5% success**, cost **1.36**
- Direct answering: **25.9% success**, cost **0.30**

The learned router improves over the strong static policy by 6.48 percentage points while reducing normalized cost by 43.0%. Compared with the learned one-shot router, composition improves success by 43.52 percentage points.

That is the cleanest positive result: many tasks require more than one operation, and a one-step routing policy misses that structure.

## The Challenge Result Is the Most Important Part

The paper also includes a locked lexical-shift challenge split. These tasks preserve the same underlying operation requirements but use more distant paraphrases.

On that split, the learned router drops:

- Learned budget router: **75.9% success**, cost **1.56**
- Static workload router: **93.5% success**, cost **3.08**
- Fixed agent: **93.5% success**, cost **4.95**
- Learned one-shot router: **41.7% success**, cost **1.19**
- Direct answering: **25.9% success**, cost **0.30**

This is a valuable negative result. The learned router remains much cheaper than static routing and still beats the learned one-shot router by 34.3 points, but it trails the static workflow under paraphrase.

The failures are interpretable:

- Aggregate tasks miss code execution.
- Multi-hop research tasks miss decomposition.
- Conflicting-source tasks miss verification.

The executor still works when the correct operations are selected. The weak point is lexical generalization in the operation predictor.

That distinction matters. It tells us where to improve the system: not by changing the executor, but by making operation prediction more robust.

## What Is Novel Here?

The paper builds on several active lines of work: model routing, retrieval routing, tool learning, planning, agent benchmarks, and trajectory diagnosis. Its novelty is the unit of control.

Endpoint routers decide which model should answer. Retrieval routers decide how much evidence to acquire. Tool planners arrange calls inside a tool-centered workflow.

This work asks a different question: which classes of reasoning and execution should make up the workflow in the first place?

That makes the routing decision heterogeneous. The policy is not choosing between model A and model B. It is deciding whether a task needs decomposition, retrieval, code, delegation, verification, or some combination of them.

The benchmark makes that decision testable by comparing against matched one-shot, static, fixed, and oracle policies under executable grading.

## Practical Implications

The results suggest a practical architecture for agentic systems:

1. Use a cheap meta-router before launching expensive workflows.
2. Predict multiple operation types, not just one tool or one model.
3. Enforce route budgets before execution.
4. Keep typed traces for debugging and audit.
5. Fall back to static workflows when the router is uncertain or the task is out of distribution.

The challenge split points toward a hybrid approach. Static workload routes are more robust to paraphrase, while learned routing is cheaper and handles some component-outage cases better. A confidence-gated mixture of learned and static routing may be stronger than either alone.

## What This Does Not Show

The paper is careful about the boundary. The benchmark uses deterministic local components, not live LLM calls, network APIs, or production users. Normalized costs are not API prices. Local latency is not deployment latency. The tasks are generated and templated, even though they are executable and machine checked.

So the claim is not "this router is ready for production."

The claim is narrower and more useful: operation-level meta-routing can be evaluated reproducibly, composition helps on executable tasks, and lexical robustness is a central open problem for learned controllers.

## Next Steps

The next version should test semantic encoders, larger template diversity, multilingual and domain-shifted tasks, live tool adapters, and observation-conditioned replanning. It should also add a learned confidence gate that chooses between learned and static routes under uncertainty.

Longer term, this kind of benchmark can become a diagnostic layer for agentic systems. Instead of treating the agent as one black-box response generator, we can ask which decisions were made, which operations were used, which costs were incurred, and where the route failed.

That is the core idea: to make the reasoning around the model as measurable as the model output itself.

