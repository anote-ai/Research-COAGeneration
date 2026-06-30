# Targeted Literature Review

## Scope and Method

This review covers work most directly related to meta-routing decisions in agentic systems: interleaving reasoning and action, tool selection, model routing, workflow planning, and agent evaluation. Sources were selected from peer-reviewed conference proceedings and OpenReview records available through June 30, 2026. The review is deliberately narrower than a general survey of LLM agents.

| Work | Primary contribution | Relationship to MetaRoute-Bench |
|---|---|---|
| ReAct (Yao et al., 2023) | Interleaves reasoning traces and environment actions. | Establishes adaptive reason/action loops; does not jointly benchmark decomposition, delegation, code execution, cost, and latency. |
| Adaptive-RAG (Jeong et al., 2024, NAACL) | Routes queries among no-retrieval, single-step, and iterative retrieval using predicted complexity. | Direct precedent for varying orchestration depth by task difficulty; our implementation uses transparent fixed thresholds rather than a learned classifier. |
| Toolformer (Schick et al., 2023) | Learns when and how to invoke APIs. | Focuses on model-level tool use rather than system-level routing policy comparison. |
| API-Bank (Li et al., 2023, EMNLP) | Runnable tool benchmark separating planning, retrieval, and API calling. | Supports explicit tool events and error analysis; our current executor simulates rather than performs API calls. |
| ToolLLM/ToolBench (Qin et al., 2024) | Trains and evaluates LLMs over a large collection of real APIs. | Provides broad tool-use coverage; MetaRoute-Bench studies route composition and operational tradeoffs. |
| RESTful-Llama (Xu et al., 2024, EMNLP Industry) | Maps natural-language requests and API documentation to REST calls. | Demonstrates the live integration layer that should replace our seeded tool simulator. |
| AgentBench (Liu et al., 2024) | Evaluates LLM agents across eight interactive environments. | Motivates multidimensional agent evaluation and failure analysis. |
| AgentDiagnose (Ou et al., 2025, EMNLP Demo) | Diagnoses decomposition, observation reading, verification, and backtracking from agent trajectories. | Directly motivates typed traces, operation frequencies, and failure-mode analysis instead of success-only reporting. |
| SWE-bench (Jimenez et al., 2024) | Uses real GitHub issues to evaluate code agents. | Motivates executable, outcome-based evaluation; our current workloads are synthetic and therefore weaker externally. |
| LLMCompiler (Kim et al., 2024) | Plans and parallelizes function calls to reduce latency and cost. | Closest systems work on orchestration efficiency; focuses on function-call execution rather than route choice among reasoning modes. |
| FrugalGPT (Chen et al., 2024) | Cascades among LLM APIs to optimize quality and cost. | Establishes cost-aware routing; routes among models rather than among decomposition, tools, code, and delegation. |
| RouteLLM (Ong et al., 2025) | Learns strong/weak model routers from preference data. | Supplies a learned model-routing baseline concept; the present artifact uses transparent policies and should add learned routing in follow-up work. |
| CP-Router (Su et al., 2026, AAAI) | Uses conformal-prediction uncertainty to route between standard and long-reasoning models. | Motivates confidence-aware routing and shows how our fixed thresholds could be replaced with calibrated decisions. |
| ZeroRouter (Yan et al., 2026, AAAI) | Routes in a model-agnostic latent space while optimizing accuracy, cost, and latency. | Supports our three-axis evaluation and the requirement to compare task-aware policies with simple routing baselines. |
| ACPBench (Kokel et al., 2025, AAAI) | Synthesizes planning questions from formal domains with provably correct answers. | Supports scalable synthetic evaluation while highlighting a weakness of our profiles: they lack formal semantics and ground-truth plans. |
| SPIRAL (Zhang et al., 2026, AAAI) | Combines planner, simulator, and critic roles in grounded reflective search. | Supports separating planning and verification; our one-pass route composition is substantially simpler and does not perform search. |
| AnyTool (Du et al., 2024) | Uses hierarchical retrieval, solving, and reflection over many APIs. | Demonstrates recovery and hierarchical tool routing; motivates our recovery ablation. |
| tau-bench (Yao et al., 2024) | Evaluates tool-using conversational agents in policy-constrained domains. | Motivates realistic stateful evaluation; live tool environments are a required extension of our offline benchmark. |

## Research Gap

Prior work typically optimizes one layer of the decision process: retrieval depth, reasoning-model selection, API use, model choice, or function-graph execution. Agent benchmarks then measure the resulting behavior in particular environments. Less work isolates and jointly compares the system-level policy governing whether to decompose, invoke a tool, execute code, delegate, verify, recover, or answer directly under a common success-cost-latency protocol.

MetaRoute-Bench addresses that evaluation gap with a small, inspectable offline benchmark. Its present contribution is methodological and diagnostic, not a claim of production deployment or a learned state-of-the-art router.

## Implementation Rationale From Prior Work

- **Difficulty-conditioned thresholds:** Adaptive-RAG shows that query complexity can select among orchestration depths; CP-Router shows that uncertainty can support calibrated routing. MetaRoute-Bench begins with fixed, inspectable thresholds to make policy behavior reproducible, but should replace need annotations with learned and calibrated estimates.
- **Explicit operation vocabulary:** API-Bank separates planning, retrieval, and API calling, while SPIRAL separates planning, simulation, and critique. MetaRoute-Bench similarly represents decomposition, tool use, code, delegation, verification, and answering as distinct events.
- **Success, cost, and latency:** FrugalGPT, RouteLLM, LLMCompiler, and ZeroRouter demonstrate that accuracy-only comparisons miss important operating tradeoffs. The benchmark therefore reports all three dimensions and treats scalar utility as secondary.
- **Synthetic paired evaluation:** ACPBench demonstrates the scalability of generated planning tasks when grounded in formal domains. MetaRoute-Bench uses paired seeds and generated profiles for control, but lacks ACPBench's formal correctness guarantees; this is an explicit validity limitation.
- **Typed traces and failure analysis:** AgentDiagnose shows that end-task success obscures decomposition and verification behavior. MetaRoute-Bench exports every action, retry, failure mode, and workload slice.
- **Live-system extension:** API-Bank, RESTful-Llama, SWE-bench, and tau-bench provide stronger executable environments. They define the next validation phase for replacing the offline simulator with real tasks and tools.

## Inclusion Caveat

This review should be expanded before submission with deployment and observability literature from distributed systems and with any DAI papers on orchestration. Every numerical or novelty claim in the final paper should be checked against the final bibliography search conducted immediately before submission.
