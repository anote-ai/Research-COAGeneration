# Can an AI plan against an opponent who's trying to beat it back?

*A plain-language summary of the COAGeneration project. For the technical design, see `research design document.md`; for raw results, see `results/`.*

## The problem in one sentence

Most AI "planning" demos show an AI making a good plan once, against a passive world. We're asking a harder question: can an AI make a plan that's still good once an *adaptive opponent* gets to see it and respond?

## Why that distinction matters

Imagine asking an AI to plan a chess opening. It's easy to generate a move that looks strong in isolation. It's much harder to generate a move that stays strong after your opponent replies. Military and logistics planning has the same shape: a "Course of Action" (COA) that looks effective on paper can fall apart the moment a competitor reacts to it.

A lot of existing AI-planning benchmarks score a single plan against a fixed, non-adapting yardstick. That can reward plans that are *brittle* — great against the test, bad against anything that pushes back. We wanted a benchmark that specifically measures whether a plan survives contact with an adversary trying to break it.

## The setup (all synthetic, no real-world data)

We built a small two-player game:

- **BLUE** proposes a plan (a "Course of Action," or COA): a sequence of actions like *recon, advance, defend, resupply*.
- **RED** generates a response intended to exploit weaknesses in BLUE's plan.
- A scoring function (we call it MEF — Mission Effectiveness Function) rates each plan on effectiveness, cost, and risk.
- A second score (GBC — Game-Based Comparison) compares BLUE's plan directly against RED's response.

Everything here — units, locations, scenarios — is synthetic. No real military doctrine, units, or operations are involved; this is a research testbed, not a planning tool.

## What's real right now vs. what's still a hypothesis

This is the part we want to be upfront about, because it's easy for "benchmark" projects to blur the line between *built* and *imagined*.

**Actually implemented and tested today:**
- A typed simulation engine (game state, assets, actions, multi-step plans with branching) with 57 passing unit tests.
- Three non-LLM baseline planners — purely random, "pick the best-looking plan from several candidates," and a scripted fixed sequence — that we ran head-to-head for 30 trials each. (See `results/exp0_baselines.json`.) On these synthetic scenarios, the "greedy best-MEF" baseline scored slightly higher than pure random or scripted plans, but the differences are small relative to their variance — this is a sanity check that the harness works, not yet evidence that any method is "good."
- A working hookup to Claude that lets an LLM play either side, runnable today via `python scripts/run_demo.py --llm`.

**Designed but not yet run:**
- The actual research question — does *iterative, adversarial self-play with an LLM* produce more robust plans than one-shot LLM generation or the simple baselines above? We have the pieces (an LLM policy, a self-play loop, evaluation metrics) but haven't yet wired them into a full experiment with held-out opponents, multiple seeds, and statistical testing.
- A held-out adversary test set, ablations isolating which ingredient (self-play vs. LLM quality vs. iteration) actually drives any improvement, and the diversity/overfitting checks described in our design doc.

We're publishing the honest version of this story rather than waiting for a finished paper, because the negative-result risks here (self-play overfitting to its own training opponent, or a scripted heuristic matching an LLM at a fraction of the cost) are scientifically interesting on their own.

## What we'd consider a meaningful finding

Not "the AI won." We'd consider it meaningful if we can show, with held-out opponents and proper statistics, that adversarial self-play produces plans whose *worst-case* performance is reliably better than one-shot generation — or if we instead find that simple, cheap baselines are competitive, which would be an important caution against over-engineering planning pipelines with expensive agentic loops.

## Try it yourself

```bash
git clone https://github.com/anote-ai/research-coageneration
cd research-coageneration
pip install -e .
python scripts/run_demo.py          # no API key needed
python experiments/exp0_baselines.py
pytest tests/ -v
```
