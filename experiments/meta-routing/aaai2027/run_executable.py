"""Run the held-out executable benchmark used by the AAAI manuscript."""

from __future__ import annotations

import argparse
from pathlib import Path

from metarouter.executable_benchmark import (
    export_executable_results,
    export_executable_tasks,
    run_executable_benchmark,
)
from metarouter.executable_evaluation import summarize_executable_all
from metarouter.executable_tasks import generate_executable_tasks
from metarouter.text_router import executable_policies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("results/meta-routing/aaai2027/executable")
    )
    parser.add_argument("--train-per-workload", type=int, default=72)
    parser.add_argument("--dev-per-workload", type=int, default=24)
    parser.add_argument("--test-per-workload", type=int, default=36)
    parser.add_argument("--challenge-per-workload", type=int, default=36)
    args = parser.parse_args()

    train_tasks = generate_executable_tasks("train", args.train_per_workload)
    dev_tasks = generate_executable_tasks("dev", args.dev_per_workload)
    test_tasks = generate_executable_tasks("test", args.test_per_workload)
    challenge_tasks = generate_executable_tasks(
        "challenge", args.challenge_per_workload
    )
    policies, model, threshold = executable_policies(train_tasks, dev_tasks)
    traces = run_executable_benchmark(test_tasks, policies)

    export_executable_tasks(train_tasks, args.output / "train")
    export_executable_tasks(dev_tasks, args.output / "dev")
    export_executable_tasks(test_tasks, args.output / "test")
    export_executable_results(traces, args.output, model, dev_tasks, threshold)

    challenge_traces = run_executable_benchmark(challenge_tasks, policies)
    challenge_output = args.output.parent / "challenge"
    export_executable_tasks(challenge_tasks, challenge_output / "test")
    export_executable_results(
        challenge_traces,
        challenge_output,
        model,
        dev_tasks,
        threshold,
    )

    print(f"Exported {len(traces):,} traces to {args.output}")
    print(f"Learned threshold: {threshold:.2f}")
    print("policy                 success       cost   latency-ms  route-f1")
    for summary in summarize_executable_all(traces):
        print(
            f"{summary.policy:<22} "
            f"{summary.success_rate:>7.3f} "
            f"[{summary.success_ci95_low:.3f},{summary.success_ci95_high:.3f}] "
            f"{summary.mean_cost:>6.2f} "
            f"{summary.mean_latency_ms:>10.4f} "
            f"{summary.action_f1:>8.3f}"
        )
    print("challenge policy          success       cost   latency-ms  route-f1")
    for summary in summarize_executable_all(challenge_traces):
        print(
            f"{summary.policy:<22} "
            f"{summary.success_rate:>7.3f} "
            f"[{summary.success_ci95_low:.3f},{summary.success_ci95_high:.3f}] "
            f"{summary.mean_cost:>6.2f} "
            f"{summary.mean_latency_ms:>10.4f} "
            f"{summary.action_f1:>8.3f}"
        )


if __name__ == "__main__":
    main()
