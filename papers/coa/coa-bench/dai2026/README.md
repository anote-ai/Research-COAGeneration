# COA-Bench DAI 2026 Industry Draft

This folder contains the DAI 2026 Industry Track version of the COA-Bench
paper.

## Venue Fit

DAI Industry Track is the stronger fit for the current COA-Bench draft because
the contribution is a benchmark/report/artifact rather than a mature AAAI-style
algorithmic result.

## Format

- ACM `sigconf`
- Single blind: author placeholders should be replaced before submission
- Up to 6 pages, excluding references and appendices
- Include artifact link where applicable
- Include generative AI disclosure
- Discuss defense/safety limitations clearly

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

