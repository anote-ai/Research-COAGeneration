# DAI 2026 Industry Track OpenReview Fields

Use these values when filling the DAI 2026 Industry Track OpenReview submission form.

## Title

Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA matching & COA generation

## Authors

- Natan Vidra
- Alina Kapanova
- Arun Kanhai
- Spurthi Setty

All authors must have OpenReview profiles before submission.

## Keywords

course-of-action generation, self-play, benchmark, distributed AI, planning, reproducibility

## TL;DR

COA-Bench is a reproducible synthetic benchmark for evaluating course-of-action generation policies under adversarial self-play and multi-agent council revision.

## Abstract

Course-of-action (COA) generation is a distributed planning problem: a system must propose structured candidate actions, evaluate them against an adversarial response, and surface options that remain tactically coherent under changing conditions. We present COA-Bench, a small offline benchmark and reproducibility artifact for comparing COA generation policies through self-play. Following the BattleCOA terminology, we reserve COA matching for asset-effect matching and COA generation for course-of-action generation; the present artifact does not implement either DecisionFunction directly. Instead, it represents COAs as typed action chains with conditional branches, assigns a synthetic COA quality score, compares opposing COAs with a BLUE-vs-RED advantage score and Nash-gap distance, and scores doctrinal coherence with an FM 3-0-inspired heuristic rubric. Across 50 synthetic scenarios spanning five operational templates, a sampled best-response policy that draws eight RED candidates reduces BLUE advantage from .516 to .485 and BLUE wargame win rate from .920 to .820; a two-stage multi-agent council with five BLUE proposer agents, RED-team adjudication, and critique-driven revision obtains .509 BLUE advantage and .820 BLUE win rate. We also identify and fix a benchmark-design issue in which scenario framing was stored as metadata but had no effect on generated COA content. COA-Bench is not an operational battle-management system and uses no real, classified, proprietary, or human-subject data. The contribution is an inspectable evaluation harness, preliminary benchmark evidence, and lessons for building auditable agentic planning artifacts.

## PDF

Upload:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/dai2026/submission/DAI26_COA_Submission.pdf

## Topic Areas

Primary topic area:

Methods, Evaluation, and Governance for Deployed Systems

Secondary topic areas:

- Open-Source Resources, Tools, and Reproducible Artifacts
- Real-World System Design, Deployment, and Operations

## Supplementary Material

Optional at initial submission. If uploading the LaTeX source package, use:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/dai2026/submission/DAI26_COA_Source.zip

## Code And Artifact Availability

Select:

Code/artifacts are provided as a public or accessible link

## Code Or Artifact Link

https://github.com/anote-ai/research-coageneration

## Code Or Artifact Upload

Optional at initial submission. If uploading the code artifact ZIP, use:

/Users/alina/Desktop/sab/anote/meta-transfer/Research-COAGeneration/papers/coa/dai2026/submission/DAI26_COA_Code_Submission.zip

## Code Unavailability Explanation

N/A

## AI Use Disclosure

Generative AI tools materially assisted with software implementation, experiment scripting, terminology review, and manuscript drafting. The authors reviewed the code, verified the generated results against the released artifacts, checked citations, and are responsible for the final claims and text.

## Additional Information

The submission reports an offline synthetic benchmark and reproducibility artifact. It uses no real intelligence data, classified data, proprietary data, human-subject data, or operational systems. The implementation and result artifacts are linked in the public repository.

## License

CC BY 4.0
