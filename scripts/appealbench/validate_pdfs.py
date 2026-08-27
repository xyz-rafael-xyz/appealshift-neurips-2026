#!/usr/bin/env python3
"""Validate the AppealShift supporting paper and one-page abstract PDFs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader


EXPECTED_TITLE = "Matched Sources Expose Distinct Admissibility Failures in Small-Model Appeal Review"
EXPECTED_REPOSITORY_URL = "https://github.com/xyz-rafael-xyz/appealshift-neurips-2026"


def inspect_fonts(path: Path) -> tuple[int, list[str], list[str], list[str]]:
    lines = subprocess.run(
        ["pdffonts", str(path)], check=True, capture_output=True, text=True
    ).stdout.splitlines()[2:]
    unembedded = []
    nonsubset = []
    unparsed = []
    for line in lines:
        match = re.search(
            r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            unparsed.append(line)
            continue
        embedded, subset, _unicode = [item.casefold() for item in match.groups()]
        if embedded != "yes":
            unembedded.append(line)
        if subset != "yes":
            nonsubset.append(line)
    return len(lines), unembedded, nonsubset, unparsed


def inspect_pdf(path: Path, expected_pages: int) -> tuple[list[dict[str, object]], list[str], dict[str, object]]:
    reader = PdfReader(path)
    errors = []
    pages = []
    for number, page in enumerate(reader.pages, 1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        text = page.extract_text() or ""
        pages.append({"page": number, "width": width, "height": height, "text": text})
        if abs(width - 612) > 1 or abs(height - 792) > 1:
            errors.append(f"{path.name} page {number} is not US letter")
    if len(pages) != expected_pages:
        errors.append(f"{path.name} has {len(pages)} pages, expected {expected_pages}")
    joined = "\n".join(str(page["text"]) for page in pages)
    if EXPECTED_TITLE not in " ".join(joined.split()):
        errors.append(f"{path.name} is missing the expected title")
    if path.stat().st_size > 50 * 1024 * 1024:
        errors.append(f"{path.name} exceeds 50 MiB")
    font_rows, unembedded, nonsubset, unparsed = inspect_fonts(path)
    if unembedded:
        errors.append(f"{path.name} has {len(unembedded)} unembedded fonts")
    if nonsubset:
        errors.append(f"{path.name} has {len(nonsubset)} non-subset fonts")
    if unparsed:
        errors.append(f"{path.name} has {len(unparsed)} unparsed font rows")
    metadata = reader.metadata or {}
    details = {
        "bytes": path.stat().st_size,
        "font_rows": font_rows,
        "metadata_author": str(metadata.get("/Author", "")).strip(),
        "pages": len(pages),
        "page_size_points": [pages[0]["width"], pages[0]["height"]] if pages else None,
    }
    return pages, errors, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--abstract", type=Path, required=True)
    parser.add_argument("--abstract-source", type=Path, required=True)
    parser.add_argument("--paper-source", type=Path, default=Path("papers/appealshift/paper.tex"))
    parser.add_argument("--form", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paper_pages, paper_errors, paper_details = inspect_pdf(args.paper, 12)
    abstract_pages, abstract_errors, abstract_details = inspect_pdf(args.abstract, 1)
    errors = paper_errors + abstract_errors

    reference_pages = [page["page"] for page in paper_pages if "References" in str(page["text"])]
    appendix_pages = [page["page"] for page in paper_pages if "Model revisions" in str(page["text"])]
    if reference_pages != [10]:
        errors.append(f"supporting-paper references must start on page 10, found {reference_pages}")
    if appendix_pages != [12]:
        errors.append(f"supporting-paper appendix must start on page 12, found {appendix_pages}")

    paper_text = "\n".join(str(page["text"]) for page in paper_pages)
    compact_paper_text = re.sub(r"\s+", "", paper_text)
    public_repository_url_visible = EXPECTED_REPOSITORY_URL in compact_paper_text
    if not public_repository_url_visible:
        errors.append("supporting paper does not print the public repository URL")

    paper_source = args.paper_source.read_text(encoding="utf-8")
    twelve_cluster_caveat_present = (
        "With only 12 clusters, percentile coverage is approximate." in paper_source
    )
    if not twelve_cluster_caveat_present:
        errors.append("supporting paper is missing the 12-cluster interval caveat")
    if not all(
        value in paper_source
        for value in (
            "194 of 768 preliminary commitments",
            "net gain of six correct decisions",
            "from 316 to 258 decisions",
            "26 corrections and 84 new errors",
            "locally validated form payload supplied with the artifact",
            "Submission through the live form remains an author action",
        )
    ):
        errors.append("supporting paper is missing the baseline-separated workflow or live-form caveat")

    form = json.loads(args.form.read_text(encoding="utf-8"))
    source = args.abstract_source.read_text(encoding="utf-8")
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", source, flags=re.DOTALL)
    abstract_text = " ".join(match.group(1).split()) if match else ""
    abstract_text = abstract_text.replace("$p=0.00046$", "p = 0.00046")
    expected_abstract = " ".join(form["abstract"].split())
    if expected_abstract != abstract_text:
        errors.append("one-page LaTeX source does not match the exact normalized form abstract")
    if len(form["abstract"]) > 2500:
        errors.append("form abstract exceeds 2500 characters")
    if len(form["tldr"]) > 300:
        errors.append("form TLDR exceeds 300 characters")

    report = {
        "paper": paper_details,
        "abstract": abstract_details,
        "paper_reference_pages": reference_pages,
        "paper_appendix_pages": appendix_pages,
        "public_repository_url_visible": public_repository_url_visible,
        "twelve_cluster_caveat_present": twelve_cluster_caveat_present,
        "form_abstract_characters": len(form["abstract"]),
        "form_tldr_characters": len(form["tldr"]),
        "errors": errors,
        "pass": not errors,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
