#!/usr/bin/env python3
"""Run adaptive-router ablations with the standard benchmark configuration."""

from pathlib import Path

from metarouter import (
    ablation_policies,
    export_results,
    export_tasks,
    generate_tasks,
    run_benchmark,
)


if __name__ == "__main__":
    output = Path("results/dai2026/ablations")
    tasks = generate_tasks()
    traces = run_benchmark(tasks=tasks, policies=ablation_policies(), seeds=30)
    export_tasks(tasks, output)
    summaries = export_results(traces, output)
    for summary in summaries:
        print(
            f"{summary.policy:<24} success={summary.success_rate:.3f} "
            f"cost={summary.mean_cost:.2f} latency={summary.mean_latency_s:.2f}"
        )
