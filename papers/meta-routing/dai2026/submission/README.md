# MetaRoute-Bench DAI 2026 Industry Paper

This folder contains the DAI 2026 Industry Track version of the MetaRoute-Bench paper.

## Venue Fit

The DAI contribution is the transparent evaluation framework, operational policy
comparison, trace artifact, and deployment lessons. It does not claim a learned
routing algorithm or live-system effectiveness.

## Format

- ACM `sigconf`
- Single blind: real author names and affiliations are included
- Up to 6 pages, excluding references and appendices
- Public artifact links are allowed and encouraged when applicable
- Include generative AI disclosure
- Discuss limitations, ethics, and deployment risks clearly

## Files

- `main.tex`: paper source
- `references.bib`: bibliography database
- `ACM-Reference-Format.bst`: official ACM bibliography style from the provided template zip
- `acmart.cls`: official ACM class from the provided template zip
- `figures/`: figure assets required by `main.tex`
- `DAI.pdf`: rebuilt compiled PDF
- `submission/`: upload-oriented PDF and source zip
- `SUBMISSION_CHECKLIST.md`: checklist against DAI and ACM-template requirements
- `acm-template/`: reference copy of selected files from the provided ACM template zip

## Reproduce Results

The reported numbers come from committed experiment artifacts generated with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
metarouter-benchmark --seeds 30 --output results/meta-routing/dai2026/main
python experiments/meta-routing/dai2026/run_ablations.py
python experiments/meta-routing/dai2026/plot_results.py
python experiments/meta-routing/dai2026/check_paper_results.py
pytest -q
```

Important boundary: the results use a seeded offline execution model. They must
not be described as production, human-subject, or live-LLM results.

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
cp build/main.pdf DAI.pdf
```

## Submission

Submission-ready artifacts are in `submission/`:

- `DAI26_MetaRoute_Submission.pdf`
- `DAI26_MetaRoute_Source.zip`
