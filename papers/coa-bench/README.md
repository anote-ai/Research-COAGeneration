# COA-Bench Draft

The manuscript is `main.tex`; references are in `references.bib`. Author names,
affiliations, and venue metadata are placeholders and must be filled in before
any submission. This is a working draft, not a submission-ready paper.

The reported numbers come from committed experiment artifacts generated with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest tests/ -q
python experiments/coa_bench_experiment.py
```

This regenerates:

- `results/coa-bench/main/rows.csv`: per-scenario single, quality-greedy, and doctrine-aware response results.
- `results/coa-bench/main/summary.csv`: bootstrap confidence intervals for the manuscript metrics.
- `results/coa-bench/main/budget_curve.csv`: response-budget sweep for `k = 1, 2, 4, 8, 16`.
- `results/coa-bench/main/council_rows.csv`: multi-agent council traces and diagnostics.
- `results/coa-bench/main/terrain_summary.csv`: per-template averages for scenario-family inspection.
- `results/coa-bench/main/details.json`: run metadata and headline rates.

Together these files back every number in the manuscript.

## Benchmark Additions

The current COA-Bench artifact includes three RED response policies:

- `SelfPlayEngine` single-sample response.
- `SampledBestResponsePolicy`, a quality-greedy best-of-k response.
- `DoctrineAwareBestResponsePolicy`, a best-of-k response that trades synthetic quality against a lightweight doctrine proxy.

The experiment also reports candidate-set diagnostics beyond the selected COA:
diversity, quality-score spread, Pareto-optimal candidate count, selection
quality regret, selection doctrinal gain, response-budget sensitivity, and
per-terrain summaries across the five scenario families.

The multi-agent council algorithm adds five BLUE proposer agents
(`maneuver`, `intelligence`, `cyber`, `sustainment`, `protection`), RED-team
responses for each BLUE candidate, and an adjudicator objective that trades
quality, doctrine, candidate diversity, and adversarial pressure. The current
version is two-stage: the adjudicator shortlists the top two BLUE candidates,
adds deterministic mitigation actions keyed to the strongest RED critique, and
then reruns RED-team adjudication over the revised candidates. The trace file
therefore includes initial diversity, revised diversity, consensus gap,
adversarial pressure, robustness margin, pressure reduction, and the selected
round.

Important boundary: all results come from the offline `coageneration`
self-play simulator over 50 synthetic scenarios. They are not measurements of
real planner behavior, and the FM 3-0-inspired doctrinal rubric is an
unvalidated heuristic feature extractor, not a substitute for scoring by
doctrine experts. See the manuscript's Limitations section for the full list
of caveats, including a methodological gap (scenario framing previously had
no effect on generated content) that this draft documents and partially
fixes rather than hides.

## Status

This is an early-stage draft built to establish a real, reproducible
experiment harness before committing to a paper structure. Candidate venues
(per the repository README) are DAI 2026 and AAAI 2027, but neither has been
selected for this specific manuscript yet.
