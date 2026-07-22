"""Fail if AAAI manuscript numbers drift from exported executable results."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["policy"]: row for row in csv.DictReader(handle)}


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    result_dir = root / "results/meta-routing/aaai2027/executable"
    summaries = _rows(result_dir / "summary.csv")
    ablations = _rows(root / "results/meta-routing/aaai2027/ablations/summary.csv")
    with (result_dir / "comparisons.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        comparisons = {row["baseline"]: row for row in csv.DictReader(handle)}
    details = json.loads((result_dir / "details.json").read_text(encoding="utf-8"))
    challenge = _rows(root / "results/meta-routing/aaai2027/challenge/summary.csv")
    with (root / "results/meta-routing/aaai2027/challenge/comparisons.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        challenge_comparisons = {
            row["baseline"]: row for row in csv.DictReader(handle)
        }
    paper = (root / "papers/meta-routing/aaai2027/main.tex").read_text(encoding="utf-8")

    assert float(summaries["learned_budget"]["success_rate"]) == 1.0
    assert round(float(summaries["static_workload"]["success_rate"]), 3) == 0.935
    assert round(float(summaries["learned_one_shot"]["success_rate"]), 3) == 0.565
    assert round(float(summaries["learned_budget"]["mean_cost"]), 2) == 1.76
    assert round(float(summaries["static_workload"]["mean_cost"]), 2) == 3.08
    assert round(float(comparisons["static_workload"]["success_difference"]), 4) == 0.0648
    assert round(float(comparisons["learned_one_shot"]["success_difference"]), 4) == 0.4352
    assert round(float(ablations["word_only"]["success_rate"]), 3) == 0.870
    assert details["configuration"]["test_tasks"] == 108
    assert details["configuration"]["learned_threshold"] == 0.4
    assert details["action_counts"]["learned_budget"]["use_tool"] == 77
    assert details["action_counts"]["oracle"]["use_tool"] == 49
    assert round(float(challenge["learned_budget"]["success_rate"]), 3) == 0.759
    assert round(float(challenge["static_workload"]["success_rate"]), 3) == 0.935
    assert round(
        float(challenge_comparisons["static_workload"]["success_difference"]), 4
    ) == -0.1759

    for required_text in (
        "504 tasks",
        "93.5\\%",
        "43.52 points",
        "1.76 normalized cost units",
        "\\tau=.40",
        "77 tasks versus 49",
        "Word features only & .870",
        "Learned budget & .759",
        "17.59 points lower",
    ):
        assert required_text in paper, f"paper is missing result text: {required_text}"
    for stale_text in ("43,200", "seeded offline execution model", "180 synthetic"):
        assert stale_text not in paper, f"stale simulator claim remains: {stale_text}"
    print("AAAI manuscript numbers match executable result artifacts.")


if __name__ == "__main__":
    main()
