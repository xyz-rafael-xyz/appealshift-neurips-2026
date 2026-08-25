#!/usr/bin/env python3
"""Build the current AppealShift reproducibility and submission archives."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_archive import build
from validate_archive import validate_archive


ROOT = Path(__file__).resolve().parents[2]

REPRO_ARCHIVE = Path("submissions/AppealShift_AI4Peace_2026_reproducibility.zip")
SUBMISSION_ARCHIVE = Path("submissions/AppealShift_AI4Peace_2026_submission.zip")
CHECKSUM_PATH = Path("submissions/AppealShift_SHA256SUMS.txt")
PAPER_BUILD = Path("papers/appealshift/build/paper.pdf")
ABSTRACT_BUILD = Path("papers/appealshift/build-abstract/abstract.pdf")
PAPER_SUBMISSION = Path("submissions/AppealShift_AI4Peace_2026_supporting_paper.pdf")
ABSTRACT_SUBMISSION = Path("submissions/AppealShift_AI4Peace_2026_one_page_abstract.pdf")

CHECKSUM_MEMBERS = (
    Path("submissions/AppealShift_AI4Peace_2026_form_submission.json"),
    Path("submissions/AppealShift_SUBMISSION_HANDOFF.md"),
    Path("reports/appealbench/TECHNICAL_REPORT.md"),
    Path("reports/appealbench/FULL_RESULTS.md"),
    Path("submissions/AppealShift_AI4Peace_2026_one_page_abstract.pdf"),
    Path("submissions/AppealShift_AI4Peace_2026_supporting_paper.pdf"),
    REPRO_ARCHIVE,
    Path("validation/appealbench/form_submission_validation.json"),
    Path("validation/appealbench/pdf_validation.json"),
    Path("validation/appealbench/repro_archive_validation.json"),
)

SUBMISSION_MEMBERS = (
    Path("papers/appealshift/abstract.tex"),
    Path("papers/appealshift/paper.tex"),
    Path("papers/appealshift/references.bib"),
    Path("papers/appealshift/template/neurips_2026.sty"),
    Path("reports/appealbench/CITATION_AUDIT.md"),
    Path("reports/appealbench/FULL_RESULTS.md"),
    Path("reports/appealbench/RESULT_CLAIM_AUDIT.md"),
    Path("reports/appealbench/TECHNICAL_REPORT.md"),
    Path("submissions/AppealShift_AI4Peace_2026_form_submission.json"),
    Path("submissions/AppealShift_AI4Peace_2026_one_page_abstract.pdf"),
    REPRO_ARCHIVE,
    Path("submissions/AppealShift_AI4Peace_2026_supporting_paper.pdf"),
    CHECKSUM_PATH,
    Path("submissions/AppealShift_SUBMISSION_HANDOFF.md"),
    Path("validation/appealbench/LIVE_REQUIREMENTS_RECHECK.md"),
    Path("validation/appealbench/form_submission_validation.json"),
    Path("validation/appealbench/one_page_abstract_manuscript_validation.json"),
    Path("validation/appealbench/pdf_validation.json"),
    Path("validation/appealbench/repro_archive_validation.json"),
    Path("validation/appealbench/supporting_paper_manuscript_validation.json"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    os.chdir(ROOT)
    shutil.copy2(PAPER_BUILD, PAPER_SUBMISSION)
    shutil.copy2(ABSTRACT_BUILD, ABSTRACT_SUBMISSION)
    with tempfile.TemporaryDirectory(prefix="appealshift-review-") as temp:
        stage = Path(temp) / "repository"
        subprocess.run(
            [
                sys.executable,
                "scripts/build_review_repositories.py",
                "appealshift",
                "--destination",
                str(stage),
            ],
            check=True,
        )
        repro_manifest = build(stage, REPRO_ARCHIVE, (Path("."),))

    repro_manifest["archive"] = REPRO_ARCHIVE.as_posix()
    write_json(Path("validation/appealbench/repro_archive_manifest.json"), repro_manifest)
    repro_validation = validate_archive(
        REPRO_ARCHIVE,
        ("README.md", "reproduce.sh", "paper.pdf"),
        allow_identity=True,
    )
    write_json(Path("validation/appealbench/repro_archive_validation.json"), repro_validation)
    if repro_validation["status"] != "pass":
        raise SystemExit("AppealShift reproducibility archive failed validation")

    CHECKSUM_PATH.write_text(
        "".join(f"{sha256(path)}  {path.as_posix()}\n" for path in CHECKSUM_MEMBERS),
        encoding="utf-8",
    )

    submission_manifest = build(ROOT, SUBMISSION_ARCHIVE, SUBMISSION_MEMBERS)
    submission_manifest["archive"] = SUBMISSION_ARCHIVE.as_posix()
    write_json(Path("validation/appealbench/submission_archive_manifest.json"), submission_manifest)
    submission_validation = validate_archive(
        SUBMISSION_ARCHIVE,
        (
            "submissions/AppealShift_AI4Peace_2026_form_submission.json",
            "submissions/AppealShift_AI4Peace_2026_reproducibility.zip",
            "submissions/AppealShift_AI4Peace_2026_supporting_paper.pdf",
        ),
        allow_identity=True,
    )
    write_json(
        Path("validation/appealbench/submission_archive_validation.json"),
        submission_validation,
    )
    if submission_validation["status"] != "pass":
        raise SystemExit("AppealShift submission archive failed validation")

    print(
        json.dumps(
            {
                "reproducibility": {
                    "members": repro_validation["members"],
                    "sha256": sha256(REPRO_ARCHIVE),
                },
                "submission": {
                    "members": submission_validation["members"],
                    "sha256": sha256(SUBMISSION_ARCHIVE),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
