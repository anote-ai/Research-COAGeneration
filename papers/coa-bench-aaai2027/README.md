# COA-Bench Draft (AAAI 2027 target)

This is an AAAI-2027-targeted rewrite of `papers/coa-bench/main.tex`, using the
AAAI author-kit template (`aaai2027.sty`/`aaai2027.bst`, copied from
`papers/aaai2027/`) and a validity-threat structure (construct / internal /
external / statistical) mirroring the companion MetaRoute-Bench AAAI paper.
Content and every reported number are unchanged from `papers/coa-bench/main.tex`
— this is a restructuring and terminology addition, not a new experiment.

The added content is a formal MEF/GBC problem statement plus an explicit,
tabulated correspondence (Table "correspondence") between COA-Bench's scalar
MEF/GBC scores and the Match Effectors / Generate BattleCOA DecisionFunctions
described in an internal TM-DA briefing (`BattleCOA Boot Camp 2025.pdf`, cited
as `tmda2025bootcamp`). No formula in `src/coageneration` was changed; MEF and
GBC are computed exactly as before. The paper is explicit about where the
analogy stops: COA-Bench does not implement TM-DA's hypergraph BattleCOAPath
assembly, worldline-completeness checking, or EffectEffectorMatch ranking.

The `tmda2025bootcamp` bib entry has placeholder author/institution fields —
the source document has no visible byline — and must be completed with
verified attribution before submission. Author names and affiliations are
anonymized per AAAI submission convention and must be filled in for
camera-ready.

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
