# DAI 2026 Submission Checklist

Checked against the official ACM SIG Proceedings template bundle, the saved OpenReview form PDF from 2026-07-28, and the live DAI 2026 Industry Track instructions checked on 2026-07-29.

## Passes

- Uses `\documentclass[sigconf]{acmart}`.
- Uses ACM `ACM-Reference-Format` bibliography style.
- Includes ACM conference metadata for DAI 2026.
- Includes abstract before `\maketitle`.
- Includes CCS concepts and keywords.
- Current PDF is 5 pages on Letter paper, within the DAI Industry Track limit of 6 pages excluding references and appendices.
- Includes an artifact link, which DAI encourages when applicable.
- Contains ethics/threats-to-validity and generative AI disclosure sections.
- Citation keys used in `main.tex` are all present in `references.bib`.
- Aligns with DAI Industry Track single-blind policy: real author names and affiliations are included.
- Aligns with the DAI Industry Track OpenReview form: title, authors, keywords, abstract, PDF, topic areas, code/artifact availability, and AI-use disclosure are accounted for in `submission/OPENREVIEW_FIELDS.md`.

## Completed

- Real author names, affiliations, cities, countries, and emails are included for single-blind DAI Industry Track review.
- `\shortauthors` is set to `Vidra et al.`.
- Removed the unfinished acknowledgments placeholder from the submission PDF.
- Updated the evaluation protocol text so it says four response methods, matching the four enumerated items.

## Optional Before Final Upload

- Add `\acmSubmissionID{...}` only if the DAI/OpenReview system requests it.
- Confirm the public GitHub artifact URL is live and accessible to reviewers.
- Confirm the paper is not under review at another archival venue and has not already appeared in one.
- Confirm conflicts of interest for all authors in OpenReview.
- Confirm whether to upload the code/artifact ZIP or rely on the public repository link.

## Source Package Contents

The submission source package should include:

- `main.tex`
- `references.bib`
- `ACM-Reference-Format.bst`
- `acmart.cls`
- `main.bbl`
- `README.md`
- `SUBMISSION_CHECKLIST.md`
- `OPENREVIEW_FIELDS.md`
