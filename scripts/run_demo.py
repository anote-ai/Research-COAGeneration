#!/usr/bin/env python3
"""Demo: 5-round self-play episode + GBC scores."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from coageneration.core import Force, SelfPlayEngine, compute_mef_score
from coageneration.data import make_coa, make_game_state
from coageneration.evaluate import episode_summary, gbc_score

try:
    from rich.console import Console
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def main() -> None:
    initial_state = make_game_state(n_blue=5, n_red=5, seed=42)
    engine = SelfPlayEngine(seed=42)

    states = engine.run_episode(initial_state, n_rounds=5)
    summary = episode_summary(states)

    blue_coa = make_coa(force=Force.BLUE, n_actions=3, seed=42)
    red_coa = make_coa(force=Force.RED, n_actions=3, seed=99)
    gbc = gbc_score(blue_coa, red_coa)

    if HAS_RICH:
        console = Console()
        console.print("[bold]Episode Summary[/bold]")
        for k, v in summary.items():
            console.print(f"  {k}: {v}")
        console.print(f"\n[bold]GBC Score (BLUE vs RED):[/bold] {gbc:.4f}")
        console.print(f"BLUE MEF: {blue_coa.mef_score:.4f}")
        console.print(f"RED MEF:  {red_coa.mef_score:.4f}")
    else:
        print("Episode Summary:", summary)
        print(f"GBC Score: {gbc:.4f}")
        print(f"BLUE MEF: {blue_coa.mef_score:.4f}")
        print(f"RED MEF:  {red_coa.mef_score:.4f}")


if __name__ == "__main__":
    main()
