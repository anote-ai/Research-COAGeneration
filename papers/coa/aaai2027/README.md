# AAAI 2027 COA Paper

The anonymous submission draft is `main.tex`. Submission-local copies of
`aaai2027.sty`, `aaai2027.bst`, `references.bib`, `main.bbl`, and the completed
`ReproducibilityChecklist.tex` are included in this directory. The unmodified
official examples remain under `author-kit/`.

## Intended Contribution

An adversarial course-of-action generation benchmark that evaluates candidate
plans through multi-agent critique, response-budget curves, terrain-aware stress
tests, and game-theoretic robustness metrics under synthetic wargame
conditions.

## Evidence Included

- 50 synthetic COA scenarios generated from 10 seeds and five operational templates
- Direct, heuristic, stochastic, adversarial, self-play, and council-based baselines
- Multi-agent traces with generator, adversary, logistics, reconnaissance, and arbiter roles
- Robustness, feasibility, doctrinal-coverage, diversity, regret, and exploitability metrics
- Response-budget curves, bootstrap confidence intervals, terrain summaries, and run metadata
- Completed AAAI reproducibility checklist

`author-kit/` contains the official AAAI-27 anonymous and camera-ready templates.
The submission manuscript must be anonymous and should not expose organization,
author, repository, or local path identifiers during review.

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The checklist can be compiled separately with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=build ReproducibilityChecklist.tex
```

Run these from the repository root to prepare submission artifacts:

```bash
python experiments/coa/aaai2027/prepare_submission.py
python experiments/coa/aaai2027/package_anonymous.py
```

## Submission Readiness

The submission directory contains:

- `AAAI27_COA_Anonymous.pdf`: anonymous main paper
- `AAAI27_COA_ReproducibilityChecklist.pdf`: separate completed checklist
- `code_data_supplement.zip`: identity-scanned reproducibility package
- `OPENREVIEW_FIELDS.md`: copy-paste values and upload paths for the
  OpenReview full-submission form

The manuscript and supplement use synthetic, offline scenarios only. They do not
contain classified data, real intelligence data, or live military planning
outputs.
