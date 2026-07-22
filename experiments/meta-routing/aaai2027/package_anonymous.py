"""Build a deterministic, identity-scanned AAAI code and data supplement."""

from __future__ import annotations

import zipfile
from pathlib import Path


FILES = (
    "pyproject.toml",
    "requirements.txt",
    "src/metarouter/models.py",
    "src/metarouter/executable_models.py",
    "src/metarouter/executable_tasks.py",
    "src/metarouter/executable_executor.py",
    "src/metarouter/text_router.py",
    "src/metarouter/executable_evaluation.py",
    "src/metarouter/executable_benchmark.py",
    "experiments/meta-routing/aaai2027/run_executable.py",
    "experiments/meta-routing/aaai2027/run_ablations.py",
    "experiments/meta-routing/aaai2027/plot_executable.py",
    "experiments/meta-routing/aaai2027/run_sensitivity.py",
    "experiments/meta-routing/aaai2027/check_paper_results.py",
    "tests/test_executable_metarouter.py",
    "papers/meta-routing/aaai2027/main.tex",
    "papers/meta-routing/aaai2027/references.bib",
)

DIRECTORIES = (
    "results/meta-routing/aaai2027/executable",
    "results/meta-routing/aaai2027/ablations",
    "results/meta-routing/aaai2027/challenge",
    "results/meta-routing/aaai2027/sensitivity",
)

FORBIDDEN = (
    "anote",
    "alina",
    "research-coageneration",
    "/users/",
    "github.com/",
)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    output = root / "papers/meta-routing/aaai2027/submission/code_data_supplement.zip"
    output.parent.mkdir(parents=True, exist_ok=True)

    paths = [root / path for path in FILES]
    for directory in DIRECTORIES:
        paths.extend(
            path
            for path in sorted((root / directory).rglob("*"))
            if path.is_file() and path.suffix not in {".png", ".pdf"}
        )
    supplement = root / "papers/meta-routing/aaai2027/supplement"
    supplement_files = {
        supplement / "README.md": Path("README.md"),
        supplement / "LICENSE": Path("LICENSE"),
        supplement / "metarouter_init.py": Path("src/metarouter/__init__.py"),
    }

    text_paths = [path for path in paths if path.suffix in {".py", ".toml", ".txt", ".csv", ".json", ".md"}]
    text_paths.extend(supplement_files)
    for path in text_paths:
        lowered = path.read_text(encoding="utf-8").lower()
        matches = [term for term in FORBIDDEN if term in lowered]
        if matches:
            raise ValueError(f"identity scan failed for {path}: {matches}")

    timestamp = (2026, 7, 1, 12, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, destination in supplement_files.items():
            info = zipfile.ZipInfo(str(destination), timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
        for source in sorted(paths):
            relative = source.relative_to(root)
            info = zipfile.ZipInfo(str(relative), timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
