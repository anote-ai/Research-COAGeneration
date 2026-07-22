"""Create an anonymous code/data supplement for the COA AAAI submission."""

from __future__ import annotations

from pathlib import Path
import zipfile


FORBIDDEN = ("anote", "alina", "research-coageneration", "/Users/")

FILES = [
    "pyproject.toml",
    "requirements.txt",
    "src/coageneration",
    "experiments/coa/aaai2027/run_benchmark.py",
    "experiments/coa/shared/benchmark.py",
    "tests/test_core.py",
    "tests/test_data.py",
    "tests/test_evaluate.py",
    "tests/test_llm_policy.py",
    "results/coa/aaai2027/main",
    "papers/coa/aaai2027/supplement/README.md",
    "papers/coa/aaai2027/supplement/LICENSE",
]


def _iter_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for item in FILES:
        path = root / item
        if path.is_dir():
            paths.extend(
                p
                for p in path.rglob("*")
                if p.is_file()
                and "__pycache__" not in p.parts
                and p.suffix not in {".pyc", ".pyo"}
            )
        elif path.exists():
            paths.append(path)
    return paths


def _safe_text(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return True
    lowered = text.lower()
    return not any(term.lower() in lowered for term in FORBIDDEN)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    output = root / "papers/coa/aaai2027/submission/code_data_supplement.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = _iter_paths(root)
    bad = [str(path.relative_to(root)) for path in paths if not _safe_text(path)]
    if bad:
        raise SystemExit(f"Identifying strings found in supplement files: {bad}")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.relative_to(root))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
