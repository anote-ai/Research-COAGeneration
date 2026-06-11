# Research Design Document: COA Generation

## Vision Statement

Demonstrate that AI-assisted Course of Action (COA) generation for military and logistics planning produces outputs that are **LOAC-compliant, strategically coherent, and superior to single-human planning** in time-constrained scenarios — while rigorously characterizing where human expertise remains essential and AI assistance adds most value.

---

## Problem Statement & Novelty

Course of Action (COA) generation is a structured military planning process that requires:
1. Integrating intelligence, logistics, terrain, and weather data
2. Generating multiple viable options satisfying doctrinal constraints
3. Analyzing tradeoffs across risk, resource, timing, and objective dimensions
4. Producing LOAC (Law of Armed Conflict)-compliant plans

Existing AI planning research (automated planning, PDDL solvers, tactical AI) addresses narrow subproblems. No prior work has:
- **Jointly evaluated** AI-generated COAs on compliance + strategic quality
- **Compared** human-only vs. AI-only vs. human-AI collaborative generation
- **Measured** LOAC compliance systematically as a distinct evaluation dimension
- **Characterized** which COA components benefit most from AI assistance

### Novel Contributions

| Contribution | Description |
|---|---|
| **COA-Bench dataset** | 150 scenario-COA pairs with expert-annotated quality and compliance labels |
| **LOAC compliance scorer** | Automated + human-validated LOAC compliance assessment framework |
| **CCQ metric** | Composite COA Quality: weighted combination of compliance, coherence, and feasibility |
| **Human-AI collaboration protocol** | Structured workflow for optimal human-AI COA co-generation |
| **COA component value map** | Empirical characterization of which COA components benefit from AI |

### CCQ Definition

```
CCQ = w1 × LOAC_Compliance + w2 × Strategic_Coherence + w3 × Feasibility + w4 × Timeliness

where:
  LOAC_Compliance: 0-1 (automated rule check + human review)
  Strategic_Coherence: 0-1 (expert panel rating)
  Feasibility: 0-1 (resource and logistics validation)
  Timeliness: time_to_generate / time_budget
  weights: w1=0.35, w2=0.30, w3=0.25, w4=0.10 (expert-elicited)
```

---

## Research Objectives

1. Measure **LOAC compliance rate** for AI-generated COAs vs. human-generated COAs across scenario types.
2. Compare **CCQ scores** for human-only, AI-only, and human-AI collaborative generation.
3. Identify which **COA components** (intelligence assessment, course of action narrative, synchronization matrix, risk assessment) benefit most from AI assistance.
4. Characterize **time-quality tradeoffs**: does AI assistance improve quality when time is constrained?
5. Identify **failure modes** specific to AI COA generation (LOAC violations, strategic incoherence, resource infeasibility).

---

## Dataset Construction

### Scenario Coverage (150 scenarios)

| Scenario Type | Count | Complexity | Domain |
|---|---|---|---|
| Humanitarian assistance | 30 | Low | Logistics, civil-military |
| Peacekeeping operations | 30 | Medium | Multi-party, ROE-constrained |
| Disaster response (DoD) | 25 | Medium | Logistics-heavy |
| Combat operations (historical) | 35 | High | Full doctrine |
| Hybrid threat response | 30 | Very High | Multi-domain |

**Note**: Combat scenarios are historical (post-WWII declassified), non-operational, used for AI research only.

### COA Annotation Protocol

```
For each scenario:
1. Two military subject matter experts (SMEs) independently generate COAs
2. Two SMEs independently rate AI-generated COAs on CCQ dimensions
3. LOAC reviewer (JAG-qualified) assesses compliance for all COAs
4. Annotator disagreements adjudicated by senior SME
5. All annotations documented with reasoning
```

### COA Document Structure
```yaml
coa_document:
  scenario_id: string
  situation_summary: string
  mission_statement: string
  courses_of_action:
    - coa_id: string
      concept_of_operation: string
      tasks_to_subordinate_units: list
      risk_assessment:
        risk_level: LOW|MEDIUM|HIGH
        mitigation: string
      loac_considerations: string
      synchronization_matrix: table
  recommended_coa: string
  rationale: string
```

---

## Systems Under Evaluation

| System | Model | Context | Notes |
|---|---|---|---|
| GPT-4o (zero-shot) | OpenAI | Scenario only | Frontier baseline |
| Claude Sonnet 4 (zero-shot) | Anthropic | Scenario only | Our primary |
| Claude + doctrine RAG | Anthropic | Scenario + doctrine docs | Retrieval-augmented |
| Human-only | SME panel | Full briefing | Gold standard |
| Human-AI collaborative | Claude + SME review | Iterative | Proposed protocol |
| PDDL solver (baseline) | Classical planner | Formal model | Classical AI baseline |

---

## Experimental Design

### Baseline Experiment (Experiment 0)
**Protocol**: Human-only COA generation for 30 humanitarian assistance scenarios (simplest type). Establish CCQ baseline and inter-rater agreement.

**Expected result**: Human CCQ ≈ 0.82, inter-rater agreement κ ≈ 0.71. Establishes human performance floor and annotation reliability.

---

### Experiment 1: LOAC Compliance Rate
**Hypothesis**: AI-generated COAs have LOAC violation rate > 0.25 in zero-shot setting; doctrine-augmented RAG reduces this to < 0.10.

**Protocol**:
1. Run GPT-4o and Claude (zero-shot) on all 150 scenarios.
2. LOAC reviewer assesses each COA for: (a) distinction principle violations, (b) proportionality issues, (c) necessity violations, (d) ROE non-compliance.
3. Compute LOAC violation rate = COAs with any violation / total COAs.
4. Compare zero-shot vs. doctrine-RAG augmented.

**Expected results**:

| System | LOAC Violation Rate | Most Common Violation |
|---|---|---|
| GPT-4o zero-shot | 0.31 | ROE non-compliance (48% of violations) |
| Claude zero-shot | 0.27 | Proportionality issues (42%) |
| Claude + doctrine RAG | 0.08 | Remaining: edge case necessity questions |
| Human-only | 0.04 | Ambiguous scenarios only |

- Doctrine RAG reduces violations by 70% — confirming that LOAC knowledge is in doctrine documents, not model weights.

---

### Experiment 2: CCQ Comparison (Human vs. AI vs. Collaborative)
**Hypothesis**: Human-AI collaborative generation achieves CCQ ≥ 0.90 (exceeding human-only baseline of 0.82) due to AI's ability to rapidly process and integrate large information volumes.

**Protocol**:
1. Divide scenarios into 3 groups (50 each): human-only, AI-only (Claude + doctrine RAG), human-AI collaborative.
2. Compute CCQ for each group.
3. Two-tailed t-test: collaborative vs. human-only; collaborative vs. AI-only.
4. Sub-analysis by scenario complexity.

**Expected results**:

| Condition | CCQ Mean | CCQ Std | Time (min) |
|---|---|---|---|
| Human-only | 0.82 | 0.09 | 87 |
| AI-only (Claude + RAG) | 0.74 | 0.12 | 4 |
| Human-AI collaborative | 0.89 | 0.07 | 31 |

- Collaborative achieves 89% CCQ vs. 82% human (+7 pp, p < 0.01) in 31 min (64% time reduction)
- AI-only is fastest but lowest quality; unacceptable LOAC violation rate in complex scenarios
- Key finding: collaborative protocol preserves human judgment for LOAC-critical decisions while leveraging AI for logistics/synchronization

---

### Experiment 3: COA Component Value Analysis
**Hypothesis**: AI adds most value in synchronization matrix generation and logistics feasibility assessment; humans add most value in LOAC application and strategic coherence.

**Protocol**:
1. Break each COA into 6 components: situation assessment, mission analysis, COA narrative, synch matrix, risk assessment, LOAC review.
2. Rate AI-generated vs. human-generated for each component on quality score (0-1).
3. Compute AI advantage per component = AI quality - human quality.

**Expected results**:

| Component | AI Quality | Human Quality | AI Advantage |
|---|---|---|---|
| Situation assessment | 0.79 | 0.81 | -0.02 |
| Mission analysis | 0.72 | 0.85 | -0.13 |
| COA narrative | 0.71 | 0.83 | -0.12 |
| Synchronization matrix | 0.84 | 0.74 | +0.10 |
| Logistics feasibility | 0.81 | 0.77 | +0.04 |
| LOAC review | 0.65 | 0.86 | -0.21 |

- Key finding: LOAC review is the highest-risk AI-only component; synchronization matrix is where AI adds most value.
- Recommendation: human-AI protocol routes LOAC review to human, synch matrix to AI.

---

### Experiment 4: Time-Constrained Performance
**Hypothesis**: Under 15-minute time constraints, human-AI collaborative COAs are of significantly higher quality than human-only COAs (p < 0.01), while the advantage disappears under no time constraint.

**Protocol**:
1. Run human-only and collaborative generation under 3 time budgets: 15 min, 45 min, unlimited.
2. Measure CCQ for each condition.
3. Test: is the collaborative advantage statistically significant at each time budget?

**Expected results**:
- 15-minute budget: collaborative CCQ = 0.81 vs. human-only CCQ = 0.67 (p < 0.001)
- 45-minute budget: collaborative CCQ = 0.87 vs. human-only CCQ = 0.80 (p < 0.01)
- Unlimited: collaborative CCQ = 0.89 vs. human-only CCQ = 0.82 (p < 0.05)
- Key finding: AI assistance is most valuable under time pressure — most operationally relevant case.

---

## Expected Results Summary

| Metric | AI-only | Human-only | Collaborative |
|---|---|---|---|
| CCQ | 0.74 | 0.82 | 0.89 |
| LOAC violation rate | 0.27 (0.08 w/RAG) | 0.04 | 0.05 |
| Time to generate | 4 min | 87 min | 31 min |
| Under-15-min CCQ | 0.73 | 0.67 | 0.81 |

**Primary claim**: Human-AI collaborative COA generation achieves +7 pp CCQ improvement over human-only at 64% time reduction, with near-human LOAC compliance — making it the dominant approach for time-constrained operational planning.

---

## Why This Matters

**For researchers**: COA generation is a high-stakes, doctrine-constrained planning domain that pushes LLMs to their limits — a rigorous test bed for AI planning capabilities.

**For DoD/DARPA**: Operational planning is a critical capability; AI assistance that reduces planning time while maintaining quality has direct mission impact.

**Ethical framework**: All scenarios are historical or humanitarian; no research supports autonomous lethal decision-making. Human-in-the-loop is a design requirement, not an option.

---

## Implementation Plan

```
research-coageneration/
├── data/
│   ├── scenarios/       # 150 scenario briefings
│   ├── coa_docs/        # Human + AI generated COAs
│   └── annotations/     # CCQ ratings, LOAC assessments
├── generation/
│   ├── coa_generator.py # LLM COA generation
│   ├── doctrine_rag.py  # Doctrine document retrieval
│   └── collaborative.py # Human-AI protocol implementation
├── evaluation/
│   ├── loac_checker.py  # Automated LOAC rule checking
│   ├── ccq.py           # CCQ computation
│   └── component_eval.py
├── experiments/
│   ├── exp0_baseline.py
│   ├── exp1_loac.py
│   ├── exp2_ccq_comparison.py
│   ├── exp3_components.py
│   └── exp4_time_constrained.py
```

---

## Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Scenario collection + SME recruitment | 6 weeks | 150 scenarios, SME panel |
| COA annotation | 6 weeks | Human COAs + quality labels |
| System implementation | 4 weeks | All generation systems |
| Experiments | 4 weeks | All results |
| Paper writing | 4 weeks | AAAI 2027 submission |

**Target venue**: AAAI 2027 or IJCAI 2027

---

## Open Questions & Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| SME recruitment difficulty | High | ROTC programs, defense contractors, veterans' networks |
| Classification concerns | Medium | Use only historical + humanitarian scenarios |
| LOAC reviewer availability | High | Partner with law school military law clinics |
| Scenario realism | Medium | SME validation panel |

---

## Related Issues

- DARPA LYFT connection: COA generation as a LYFT testbed task
- Ethics review: dual-use research concerns
- Reproducibility: scenario anonymization
- Related work audit: PDDL planning, military AI literature
