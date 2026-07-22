"""Compile, metadata-clean, and preflight the anonymous COA AAAI PDFs."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter


FORBIDDEN = (b"anote", b"alina", b"research-coageneration", b"/users/")


def _clean(source: Path, destination: Path) -> None:
    reader = PdfReader(source)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.metadata = {}
    writer.pdf_header = "%PDF-1.7"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        writer.write(handle)


def _font_records(reader: PdfReader) -> dict[tuple[str, str], bool]:
    records: dict[tuple[str, str], bool] = {}
    for page in reader.pages:
        fonts = page["/Resources"].get("/Font", {})
        for reference in fonts.values():
            font = reference.get_object()
            key = (str(font.get("/BaseFont")), str(font.get("/Subtype")))
            descriptors = []
            if font.get("/FontDescriptor"):
                descriptors.append(font["/FontDescriptor"].get_object())
            for descendant in font.get("/DescendantFonts", []):
                child = descendant.get_object()
                if child.get("/FontDescriptor"):
                    descriptors.append(child["/FontDescriptor"].get_object())
            embedded = any(
                any(name in descriptor for name in ("/FontFile", "/FontFile2", "/FontFile3"))
                for descriptor in descriptors
            )
            records[key] = records.get(key, False) or embedded
    return records


def _preflight(path: Path, maximum_pages: int | None = None) -> None:
    reader = PdfReader(path)
    assert not reader.is_encrypted
    if maximum_pages is not None:
        assert len(reader.pages) <= maximum_pages
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        assert abs(width - 612.0) < 0.1 and abs(height - 792.0) < 0.1
    metadata = dict(reader.metadata or {})
    assert not any(key in metadata for key in ("/Author", "/Title", "/CreationDate", "/ModDate"))
    fonts = _font_records(reader)
    assert all(subtype != "/Type3" for _name, subtype in fonts)
    assert all(fonts.values())
    lowered = path.read_bytes().lower()
    assert not any(term in lowered for term in FORBIDDEN)
    print(f"Preflight passed: {path} ({len(reader.pages)} pages, {len(fonts)} fonts)")


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    paper = root / "papers/coa/aaai2027"
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-outdir=build",
            "main.tex",
        ],
        cwd=paper,
        check=True,
    )
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-outdir=build",
            "ReproducibilityChecklist.tex",
        ],
        cwd=paper,
        check=True,
    )

    submission = paper / "submission"
    main_pdf = submission / "AAAI27_COA_Anonymous.pdf"
    checklist_pdf = submission / "AAAI27_COA_ReproducibilityChecklist.pdf"
    _clean(paper / "build/main.pdf", main_pdf)
    _clean(paper / "build/ReproducibilityChecklist.pdf", checklist_pdf)
    _preflight(main_pdf, maximum_pages=9)
    _preflight(checklist_pdf)


if __name__ == "__main__":
    main()
