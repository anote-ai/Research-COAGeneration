#!/usr/bin/env python3
"""Demo: 5-round self-play episode + GBC scores.

Run with random policy (default):
    python scripts/run_demo.py

Run with LLM policy (requires ANTHROPIC_API_KEY):
    python scripts/run_demo.py --llm
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from coageneration.core import Force, SelfPlayEngine
from coageneration.data import make_coa, make_game_state
from coageneration.evaluate import episode_summary, gbc_score

try:
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def _print(msg: str) -> None:
    if HAS_RICH:
        Console().print(msg)
    else:
        print(msg)


def main() -> None:
    parser = argparse.ArgumentParser(description="COAGeneration self-play demo")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-backed policy (requires ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument("--rounds", type=int, default=5, help="Number of self-play rounds")
    args = parser.parse_args()

    policy = None
    if args.llm:
        try:
            import anthropic
            from coageneration.llm_policy import LLMPolicy
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("Error: ANTHROPIC_API_KEY environment variable not set.")
                sys.exit(1)
            client = anthropic.Anthropic(api_key=api_key)
            policy = LLMPolicy(client=client, model="claude-sonnet-4-6")
            _print("[bold green]Using LLM policy (Claude)[/bold green]" if HAS_RICH else "Using LLM policy (Claude)")
        except ImportError:
            print("Error: 'anthropic' package not installed. Run: pip install anthropic")
            sys.exit(1)
    else:
        _print("[bold]Using random policy[/bold]" if HAS_RICH else "Using random policy")

    initial_state = make_game_state(n_blue=5, n_red=5, seed=42)
    engine = SelfPlayEngine(seed=42, policy=policy)

    _print(f"\nRunning {args.rounds}-round self-play episode...")
    states = engine.run_episode(initial_state, n_rounds=args.rounds)
    summary = episode_summary(states)

    blue_coa = make_coa(force=Force.BLUE, n_actions=3, seed=42)
    red_coa = make_coa(force=Force.RED, n_actions=3, seed=99)
    gbc = gbc_score(blue_coa, red_coa)

    if HAS_RICH:
        console = Console()
        console.print("\n[bold]Episode Summary[/bold]")
        for k, v in summary.items():
            console.print(f"  {k}: {v}")
        console.print(f"\n[bold]GBC Score (BLUE vs RED):[/bold] {gbc:.4f}")
        console.print(f"BLUE MEF: {blue_coa.mef_score:.4f}")
        console.print(f"RED MEF:  {red_coa.mef_score:.4f}")
    else:
        print("\nEpisode Summary:", summary)
        print(f"GBC Score: {gbc:.4f}")
        print(f"BLUE MEF: {blue_coa.mef_score:.4f}")
        print(f"RED MEF:  {red_coa.mef_score:.4f}")


if __name__ == "__main__":
    main()
