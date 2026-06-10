# COAGeneration — Research Design Document

## Goal

Develop an AI system that generates viable Courses of Action (COAs) for military planning scenarios with explicit LOAC constraint satisfaction, and demonstrate that AI-generated COAs are rated as high quality by military subject matter experts — enabling faster and more diverse option generation for human decision-makers.

## Objective

1. Build a COA generation system that outputs 3+ candidate COAs ranked by a multi-criterion scoring function (mission effectiveness, resource efficiency, LOAC compliance, operational risk)
2. Evaluate AI-generated COAs against human-generated COAs on quality metrics rated by military SMEs
3. Demonstrate AI generation is faster and produces comparable or higher diversity of options

## Background / Motivation

Military planning is time-constrained. In a contested environment, a planning team may have hours to produce a COA brief that traditionally takes days. AI-assisted COA generation can compress this timeline by generating diverse candidate options that human planners evaluate, refine, and select from.

Current AI planning tools use brittle rule-based approaches. LLM-based COA generation, constrained by LOAC requirements and military doctrine, has not been systematically evaluated.

## Experimental Design

### Baseline Experiment

**Human planning team generates COAs for 10 unclassified synthetic scenarios**

- Metric: COAs generated per hour; SME quality rating (1–5 scale); LOAC compliance rate; diversity score
- Purpose: establish the human baseline that AI must be compared against
- Expected result: human teams generate 2–3 COAs per 4-hour planning session; quality rating ≈ 4.0; 100% LOAC compliant

### Test Experiment 1: AI COA Generation Quality

Generate COAs for the same 10 scenarios using the AI system. Have the same SME panel rate AI-generated COAs blind (don't know which are AI vs. human).

**Expected result:** AI quality rating ≈ 3.5 (below human 4.0, but acceptable for "first draft" use); LOAC compliance 85% unconstrained, 98% with explicit LOAC constraint checker; AI generates 10–15 COAs in <5 minutes vs. 2–3 in 4 hours

### Test Experiment 2: LOAC Constraint Satisfaction

Test on 50 scenarios where a naïve planner might violate distinction, proportionality, or precaution. Run COA generation with and without LOAC constraints. Have JAG officer review outputs.

**Expected result:** unconstrained generation has ~20% LOAC violation rate; constrained reduces to <5%

### Test Experiment 3: Human-AI Collaborative Planning

Test workflow: AI generates 10 candidates → human selects and refines 3 → SME rates final output. Compare: AI-only vs. human-refined AI vs. purely human COAs.

**Expected result:** human-refined AI COAs are rated higher than both AI-only and purely human COAs — the collaborative workflow is optimal

## Expected Results

1. A COA generation system with explicit LOAC constraint satisfaction
2. SME-rated quality comparison: AI vs. human vs. AI+human collaborative
3. LOAC violation rate characterization: constrained vs. unconstrained
4. **Key finding:** "AI generates 5x more COA options in 1/50th the time — collaborative planning outperforms either AI or humans alone"
5. Practical workflow recommendation

## Why This Matters / Why People Would Care

- **Military planners:** time pressure in real operations; first-draft COAs in minutes has immediate operational value
- **Defense AI policy:** LOAC compliance rate findings directly inform policy discussions about appropriate AI use in military planning
- **AI researchers:** COA generation is a rich planning problem with clear evaluation criteria
- **AI safety:** demonstrating LOAC constraints can be reliably enforced is a proof-of-concept for constrained generation in other high-stakes domains

## Timeline

| Month | Milestone |
|---|---|
| 1–2 | System implementation + scenario construction |
| 3 | Human baseline data collection (SME ratings, human COAs) |
| 4 | AI COA generation + LOAC constraint experiments |
| 5 | Human-AI collaborative workflow experiment + SME rating collection |
| 6 | Submission to AAAI 2027 |

## Related Issues

- Design doc GitHub issue: #18
- Target conferences: see issues labeled `conference-prep`
- Reproducibility package: see issues labeled `artifact-release`
