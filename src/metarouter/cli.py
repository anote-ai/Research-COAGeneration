"""Command-line entry point for the meta-routing benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from .benchmark import export_results, export_tasks, run_benchmark
from .workloads import generate_tasks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("results/metarouter"))
    args = parser.parse_args()

    tasks = generate_tasks()
    traces = run_benchmark(tasks=tasks, seeds=args.seeds)
    export_tasks(tasks, args.output)
    summaries = export_results(traces, args.output)

    print(f"Exported {len(traces):,} traces to {args.output}")
    print("policy               success      cost   latency   utility")
    for summary in summaries:
        print(
            f"{summary.policy:<20} "
            f"{summary.success_rate:>7.3f}+-{summary.success_ci95:.3f} "
            f"{summary.mean_cost:>7.2f} "
            f"{summary.mean_latency_s:>8.2f} "
            f"{summary.utility:>8.3f}"
        )


if __name__ == "__main__":
    main()
