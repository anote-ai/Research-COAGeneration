# Results

This directory holds output artifacts from `experiments/*.py` scripts.

| File | Produced by | Status |
|---|---|---|
| `exp0_baselines.json` | `experiments/exp0_baselines.py` | Real, locally computed (no LLM calls, no network access). Compares B0 (random), B1 (greedy MEF), and B2 (scripted heuristic) baselines from `research design document.md` Section 7, using 30 seeds against randomly-sampled RED best-responses. |

## What is *not* yet here

- **B3/B4 (LLM-guided and LLM-free self-play)** results — require `ANTHROPIC_API_KEY` and were not executed in this pass. `coageneration.llm_policy.LLMPolicy` and `scripts/run_demo.py --llm` are implemented and manually runnable, but no automated experiment script calls them yet, and no results have been collected.
- **Held-out adversary generalization (RQ1/RQ3)** — the current `SelfPlayEngine.best_response` fallback is a *uniform random* response generator, not an optimizing best-response. Until an actual best-response search/optimization is implemented, "robustness" numbers in `exp0_baselines.json` should be read as "performance against a random adversary draw," not "performance against an adversarially-optimized opponent."
- **Ablations (Section 9 of the design doc)** — none implemented yet.
- **Statistical testing (paired bootstrap / significance tests)** — not implemented; `exp0_baselines.json` reports means and stdevs only.

## Reproducing `exp0_baselines.json`

```bash
pip install -e .
python experiments/exp0_baselines.py
```

This is deterministic given the seeds used in the script (seeds 0-29) and does not require any API key.
