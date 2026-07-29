# AAAI 2027 OpenReview Fields

Use these values when filling or updating the AAAI 2027 OpenReview full-submission form.

## Title

AdvPlan-Bench: Adversarial Evaluation of Structured Plan-Generation Agents

Note: the saved OpenReview printout still shows the older COA title. Update the OpenReview title to match the current anonymous PDF before final submission.

## Authors

The saved OpenReview form currently lists:

- Alina Kapanova
- Arun Kanhai
- Natan Vidra

All listed authors must have complete OpenReview profiles, including publication name, current position, institution-affiliated email address, and DBLP URL if available. Add any missing intended coauthors before the deadline; do not add authors after submission unless AAAI policy explicitly permits it.

## TL;DR

We introduce AdvPlan-Bench, a reproducible offline benchmark for evaluating structured plan-generation agents under adversarial response sampling, candidate-frontier diagnostics, and multi-agent critique-and-revision.

## Abstract

Structured plan-generation agents are often evaluated as if a plan has quality in isolation, yet many realistic planning tasks require asking how a candidate behaves when another agent can search for responses. We introduce AdvPlan-Bench, an offline benchmark for adversarial evaluation of structured plan-generation agents. The contribution is a general evaluation object: a typed plan, an adversarial response set, selector diagnostics, and traceable candidate-frontier metrics. AdvPlan-Bench represents plans as typed action chains with optional branches, assigns synthetic quality scores, compares opposing plans with BLUE-vs-RED advantage and Nash-gap diagnostics, and evaluates qualitative constraint coherence with a transparent heuristic rubric. In 150 synthetic scenarios spanning five planning templates, a sampled best-response policy that draws eight response candidates reduces BLUE advantage from .518 to .486 and BLUE win rate from .900 to .820 relative to a single-sample response. An offline LLM-policy contract baseline reaches .496 BLUE advantage and .700 BLUE win rate, while a two-stage multi-agent council obtains .509 BLUE advantage and .813 BLUE win rate. A three-rater rubric-sensitivity study over 600 rating records yields .978 inter-rater agreement. AdvPlan-Bench is not an operational planner and provides no evidence about real-world decision quality; it is a reproducible benchmark artifact for studying adversarial plan evaluation, response-budget sensitivity, candidate frontiers, and multi-agent critique-and-revision traces.

## Country Of Institutions

United States

## PDF

Upload:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/aaai2027/submission/AAAI27_COA_Anonymous.pdf

## Reproducibility Checklist

Upload:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/aaai2027/submission/AAAI27_COA_ReproducibilityChecklist.pdf

## Technical Supplement

No separate technical supplement is required. The main paper is self-contained, and the code/data supplement contains the reproducibility artifacts.

## Media Supplement

No media supplement.

## Code And Data Supplement

Upload:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/aaai2027/submission/code_data_supplement.zip

Important: AAAI's form says external code/data repository links are forbidden for review, including anonymized repositories. Use the ZIP upload, not a GitHub link.

## Self-Declared Conflict Of Interest

Complete manually in OpenReview for any authors, reviewers, or area chairs who meet AAAI/OpenReview conflict criteria. If there are none beyond system-detected conflicts, leave this field blank.

## Submission Policies Acknowledgment

Check each box only after confirming:

- all author OpenReview profiles are complete;
- the manuscript and supplement are anonymous;
- neither this manuscript nor a substantially similar version is under review at another archival venue;
- any relevant simultaneous submissions are cited anonymously as under-review work, if applicable.

## License

CC BY 4.0
