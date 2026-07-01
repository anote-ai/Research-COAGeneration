# AAAI 2027 Main-Track Paper

The anonymous submission draft is `main.tex`. Submission-local copies of
`aaai2027.sty`, `aaai2027.bst`, `references.bib`, the result figure, and the
completed `ReproducibilityChecklist.tex` are included in this directory. The
unmodified official examples remain under `author-kit/`.

## Intended Contribution

A learned, budget-aware meta-routing policy that selects reasoning,
decomposition, tools, code execution, delegation, and verification from task
inputs and execution history.

## Required Evidence

- Real natural-language tasks with executable outcomes
- Learned routing without generated operation-need annotations
- Held-out task templates, tools, and workload families
- Strong learned, static, direct, ReAct-style, and oracle baselines
- Actual token cost and wall-clock latency
- Calibration, statistical tests, generalization, and ablations
- Completed AAAI reproducibility checklist

`author-kit/` contains the official AAAI-27 anonymous and camera-ready templates.
The submission manuscript must be anonymous and must not reuse the DAI paper as
a cosmetically reformatted archival submission.

## Compile

From this directory:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The checklist can be compiled separately with:

```bash
pdflatex ReproducibilityChecklist
```

## Submission Readiness

The manuscript follows the AAAI-27 anonymous format and reports only measured
offline results. It is not yet a strong AAAI submission: the present controller
uses generated operation-need annotations, and evaluation uses a seeded
simulator rather than executable natural-language tasks. It must not be submitted
concurrently with a substantially similar archival DAI paper. Before submission,
add a research-use license, an anonymized code archive, documented parameter
selection, stronger statistical testing, and preferably learned routing with
live executable evaluation.
