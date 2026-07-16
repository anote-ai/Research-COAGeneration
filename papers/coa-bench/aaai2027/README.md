# COA-Bench AAAI 2027 Draft

This folder contains an anonymous AAAI-27 formatted version of the COA-Bench
paper.

## Venue Fit

This version is formatted for AAAI, but the current contribution is probably
too preliminary for AAAI main track unless expanded. It needs a larger
benchmark, stronger baselines, expert/rubric validation, and likely evaluation
of the LLM-backed policy.

## Format

- Official AAAI 2027 style copied locally as `aaai2027.sty`
- Anonymous submission
- Main content must be at most 7 pages
- Total paper must be at most 9 pages, with pages after 7 reserved for references
- Reproducibility checklist required for a real AAAI submission
- Supplement/code can be uploaded separately

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

