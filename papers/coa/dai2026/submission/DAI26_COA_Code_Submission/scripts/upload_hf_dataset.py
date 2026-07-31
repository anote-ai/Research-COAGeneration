"""Stage and upload Research COAGeneration COA datasets to Hugging Face.

Usage:
    python scripts/upload_hf_dataset.py --repo-id YOUR_USERNAME/research-coageneration

Authentication:
    hf auth login
    # or set HF_TOKEN in your environment
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE = REPO_ROOT / "output" / "hf_dataset"
TRACK_SOURCES = {
    "coa": REPO_ROOT / "results" / "coa",
}


DATASET_CARD = """---
license: mit
pretty_name: Research COAGeneration COA
tags:
- synthetic-data
- benchmark
- multi-agent-systems
- game-theory
- course-of-action-generation
- adversarial-planning
---

# Research COAGeneration COA Dataset

This dataset contains synthetic benchmark outputs from the Research
COAGeneration repository.

## Contents

- `data/coa/dai2026/main/` - DAI 2026 COA benchmark outputs
- `data/coa/aaai2027/main/` - AAAI 2027 COA benchmark outputs

COA result folders contain per-scenario rows, summary tables, response-budget
curves, council traces, terrain summaries, rubric validation where available,
and run metadata.

## Important Use Notice

This dataset is for academic research only. COA scenarios, assets, policies,
and strategies are synthetic and do not represent real military doctrine,
operations, or advice.

## License

MIT. See the source repository license for details.
"""


def copy_tree_clean(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for path in source.rglob("*"):
        if path.name == ".DS_Store" or path.is_dir():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def stage_dataset(tracks: list[str], stage: Path) -> None:
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    for track in tracks:
        source = TRACK_SOURCES[track]
        if not source.exists():
            raise FileNotFoundError(f"Dataset source folder not found: {source}")
        data_dir = stage / "data" / track
        copy_tree_clean(source, data_dir)

    (stage / "README.md").write_text(DATASET_CARD, encoding="utf-8")


def upload_dataset(repo_id: str, stage: Path, private: bool) -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: huggingface_hub. Install it with:\n"
            "  python -m pip install -U huggingface_hub hf_xet"
        ) from exc

    api = HfApi()
    api.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=private,
        exist_ok=True,
    )
    api.upload_folder(
        folder_path=str(stage),
        repo_id=repo_id,
        repo_type="dataset",
        ignore_patterns=[".DS_Store", "**/.DS_Store"],
        commit_message="Upload COAGeneration benchmark datasets",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload Research COAGeneration datasets to Hugging Face."
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face dataset repo id, e.g. username/research-coageneration.",
    )
    parser.add_argument(
        "--tracks",
        nargs="+",
        choices=["coa"],
        default=["coa"],
        help="Dataset tracks to stage/upload. Default: coa.",
    )
    parser.add_argument(
        "--stage",
        type=Path,
        default=DEFAULT_STAGE,
        help=f"Local staging folder. Default: {DEFAULT_STAGE}",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create the Hugging Face dataset repo as private.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare the local staged dataset but do not upload.",
    )
    args = parser.parse_args()

    stage = args.stage.resolve()
    tracks = args.tracks
    stage_dataset(tracks, stage)

    files = sorted(path.relative_to(stage) for path in stage.rglob("*") if path.is_file())
    print(f"Staged {len(files)} files in {stage}")
    for path in files:
        print(f"  {path}")

    if args.dry_run:
        print("Dry run complete. No files uploaded.")
        return

    upload_dataset(args.repo_id, stage, args.private)
    print(f"Uploaded dataset to https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
