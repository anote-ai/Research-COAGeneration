# Targeted Literature Review

## Scope and Method

This review covers work most directly related to meta-routing decisions in agentic systems: interleaving reasoning and action, tool selection, model routing, workflow planning, and agent evaluation. Sources were selected from peer-reviewed conference proceedings and OpenReview records available through June 30, 2026. The review is deliberately narrower than a general survey of LLM agents.

| Work | Primary contribution | Relationship to MetaRoute-Bench |
|---|---|---|
| ReAct (Yao et al., 2023) | Interleaves reasoning traces and environment actions. | Establishes adaptive reason/action loops; does not jointly benchmark decomposition, delegation, code execution, cost, and latency. |
| Toolformer (Schick et al., 2023) | Learns when and how to invoke APIs. | Focuses on model-level tool use rather than system-level routing policy comparison. |
| ToolLLM/ToolBench (Qin et al., 2024) | Trains and evaluates LLMs over a large collection of real APIs. | Provides broad tool-use coverage; MetaRoute-Bench studies route composition and operational tradeoffs. |
| AgentBench (Liu et al., 2024) | Evaluates LLM agents across eight interactive environments. | Motivates multidimensional agent evaluation and failure analysis. |
| SWE-bench (Jimenez et al., 2024) | Uses real GitHub issues to evaluate code agents. | Motivates executable, outcome-based evaluation; our current workloads are synthetic and therefore weaker externally. |
| LLMCompiler (Kim et al., 2024) | Plans and parallelizes function calls to reduce latency and cost. | Closest systems work on orchestration efficiency; focuses on function-call execution rather than route choice among reasoning modes. |
| FrugalGPT (Chen et al., 2024) | Cascades among LLM APIs to optimize quality and cost. | Establishes cost-aware routing; routes among models rather than among decomposition, tools, code, and delegation. |
| RouteLLM (Ong et al., 2025) | Learns strong/weak model routers from preference data. | Supplies a learned model-routing baseline concept; the present artifact uses transparent policies and should add learned routing in follow-up work. |
| AnyTool (Du et al., 2024) | Uses hierarchical retrieval, solving, and reflection over many APIs. | Demonstrates recovery and hierarchical tool routing; motivates our recovery ablation. |
| tau-bench (Yao et al., 2024) | Evaluates tool-using conversational agents in policy-constrained domains. | Motivates realistic stateful evaluation; live tool environments are a required extension of our offline benchmark. |

## Research Gap

Prior work typically optimizes one layer of the decision process: whether to act, which tool to call, which model to query, or how to execute a function graph. Agent benchmarks then measure the resulting behavior in particular environments. Less work isolates and jointly compares the system-level policy governing whether to decompose, invoke a tool, execute code, delegate, verify, recover, or answer directly under a common success-cost-latency protocol.

MetaRoute-Bench addresses that evaluation gap with a small, inspectable offline benchmark. Its present contribution is methodological and diagnostic, not a claim of production deployment or a learned state-of-the-art router.

## Inclusion Caveat

This review should be expanded before submission with deployment and observability literature from distributed systems and with any DAI papers on orchestration. Every numerical or novelty claim in the final paper should be checked against the final bibliography search conducted immediately before submission.

