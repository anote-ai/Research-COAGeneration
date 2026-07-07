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

This regenerates `results/coa-bench/main/rows.csv`, `summary.csv`, and
`details.json`, which back every number in the manuscript.

Important boundary: all results come from the offline `coageneration`
self-play simulator over 30 synthetic scenarios. They are not measurements of
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
