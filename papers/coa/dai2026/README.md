# COA-Bench DAI 2026 Industry Draft

This folder contains the DAI 2026 Industry Track version of the COA-Bench paper.

## Venue Fit

DAI Industry Track is the stronger fit for the current COA-Bench draft because
the contribution is a benchmark/report/artifact rather than a mature AAAI-style
algorithmic result.

## Format

- ACM `sigconf`
- Single blind: real author names and affiliations must be present before final upload
- Up to 6 pages, excluding references and appendices
- Public artifact links are allowed and encouraged when applicable
- Include generative AI disclosure
- Discuss defense/safety limitations clearly

## Files

- `main.tex`: paper source
- `references.bib`: bibliography database
- `ACM-Reference-Format.bst`: official ACM bibliography style from the provided template zip
- `acmart.cls`: official ACM class from the provided template zip
- `DAI.pdf`: rebuilt compiled PDF
- `submission/`: upload-oriented PDF and source zip
- `SUBMISSION_CHECKLIST.md`: checklist against DAI and ACM-template requirements
- `acm-template/`: reference copy of selected files from the provided ACM template zip

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
cp build/main.pdf DAI.pdf
```

## Submission

Submission-ready artifacts are in `submission/`:

- `DAI26_COA_Submission.pdf`
- `DAI26_COA_Source.zip`

Before final upload, replace the author, affiliation, city, country, email, and
short-author placeholders in `main.tex`, then rebuild the PDF and source zip.
