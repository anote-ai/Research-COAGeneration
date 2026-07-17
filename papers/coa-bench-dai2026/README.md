# COA-Bench Draft (DAI 2026 target)

This is a DAI-2026-targeted rewrite of `papers/coa-bench/main.tex`. Content and
all reported numbers are unchanged from that paper; the only substantive
addition is Section "MEF and GBC: Definitions and TM-DA Alignment," which
states an explicit, bounded terminology correspondence between COA-Bench's
existing MEF/GBC scores and the Match Effectors / Generate BattleCOA
DecisionFunctions described in an internal TM-DA briefing
(`BattleCOA Boot Camp 2025.pdf`, cited as `tmda2025bootcamp`). No formula in
`src/coageneration` was changed to produce this paper; MEF and GBC are computed
exactly as before.

Author names, affiliations, and venue metadata mirror `papers/coa-bench/` and
must be confirmed before any submission. The `tmda2025bootcamp` bib entry has
placeholder author/institution fields — the source document has no visible
byline — and must be completed with verified attribution before submission.

Regenerate the underlying numbers with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest tests/ -q
python experiments/coa_bench_experiment.py
python experiments/check_coa_bench_results.py   # verify paper numbers
```

See `papers/coa-bench/README.md` for the full experimental status and caveats;
they apply identically here.
