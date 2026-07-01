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
python experiments/check_coa_bench_results.py   # verify paper numbers
```

This regenerates `results/coa-bench/main/rows.csv`, `summary.csv`, and
`details.json`, which back every number in the manuscript. The check
script asserts all paper numbers match the CSV within tolerance=0.002.

If `ANTHROPIC_API_KEY` is set, the experiment also runs `LLMPolicy`
(Claude) as a third RED variant; without it the LLM column is skipped
and only the two sampling baselines are evaluated. The paper reports
results for the sampling baselines only (LLM comparison is deferred).

Important boundary: all results come from the offline `coageneration`
self-play simulator over 90 synthetic scenarios (30 seeds × 3 templates). They are not measurements of
real planner behavior, and the FM 3-0-inspired doctrinal rubric is an
unvalidated heuristic feature extractor, not a substitute for scoring by
doctrine experts. See the manuscript's Limitations section for the full list
of caveats, including a methodological gap (scenario framing previously had
no effect on generated content) that this draft documents and partially
fixes rather than hides.

## Status

Targeting DAI 2026. The experiment harness is complete (90 scenarios, 2
sampling baselines, figures, ethics section, military AI related work,
cross-citations with MetaRoute-Bench). The main open item is LLM policy
evaluation (LLMPolicy comparison requires live API access). All paper
numbers are verified against the committed CSV artifacts.
