# AAAI-27 Meta-Routing Submission Checklist

## Main PDF

- File: `submission/AAAI27_Anonymous.pdf`
- Format: AAAI-27 anonymous submission template via `\usepackage[submission]{aaai2027}`.
- Paper size: US Letter, 8.5 x 11 inches.
- Length: 7 pages total in the current PDF.
- Author block: anonymous (`Anonymous Submission`, empty affiliations).
- Reproducibility checklist: available separately as `submission/AAAI27_ReproducibilityChecklist.pdf`.

AAAI-26 instructions state that review submissions must be anonymous, use AAAI two-column style, be US Letter, and may contain up to 7 pages of technical content plus pages solely for references and the reproducibility checklist. The AAAI-27 page links the AAAI-27 Author Kit and lists the AAAI-27 main-conference submission timeline.

## arXiv / Source Compilation Package

Use `submission/AAAI27_MetaRoute_arxiv_source.zip` when a system asks for LaTeX source files. This archive is intentionally separate from the code/data supplement.

Included source files:

- `main.tex`
- `main.bbl`
- `references.bib`
- `aaai2027.sty`
- `aaai2027.bst`
- `figures/executable_tradeoffs.pdf`
- `figures/executable_tradeoffs.png`

Validation completed from a clean temporary extraction:

- `pdflatex main.tex`
- `pdflatex main.tex`

Result: compiled successfully with no undefined citations and no missing `figures/executable_tradeoffs.pdf` error.

## Code/Data Supplement

Use `submission/code_data_supplement.zip` only for the AAAI code/data supplement. It is not a complete LaTeX source package and should not be uploaded as the arXiv/source compilation bundle.
