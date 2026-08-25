#!/usr/bin/env python3
"""Validate AppealShift release archives for path safety and identity leakage."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import PurePosixPath, Path
from typing import Dict, List, Sequence


TEXT_SUFFIXES = {".bib", ".csv", ".json", ".jsonl", ".md", ".py", ".tex", ".txt"}
BANNED_PARTS = {"__pycache__", ".DS_Store", ".git", ".venv"}
BANNED_WEIGHT_SUFFIXES = {".bin", ".gguf", ".safetensors"}
IDENTITY_USER = b"rafa" + b"el"
IDENTITY_PATTERNS = (
    re.compile(rb"/Users/" + IDENTITY_USER + rb"(?:/|\b)", flags=re.IGNORECASE),
    re.compile(rb"\b" + IDENTITY_USER + rb"@[A-Za-z0-9.-]+", flags=re.IGNORECASE),
)


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "" not in path.parts


def validate_archive(
    path: Path, required: Sequence[str], allow_identity: bool = False
) -> Dict[str, object]:
    errors: List[str] = []
    identity_hits: List[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            errors.append("archive contains duplicate paths")
        for required_name in required:
            if required_name not in names:
                errors.append(f"missing required path {required_name}")
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            if not safe_name(name):
                errors.append(f"unsafe path {name}")
            if any(part in BANNED_PARTS for part in pure.parts):
                errors.append(f"banned path component in {name}")
            if pure.suffix.lower() in BANNED_WEIGHT_SUFFIXES:
                errors.append(f"model-weight-like file in {name}")
            file_type = (info.external_attr >> 16) & 0o170000
            if file_type == 0o120000:
                errors.append(f"symbolic link in {name}")
            if info.is_dir() or pure.suffix.lower() not in TEXT_SUFFIXES:
                continue
            data = archive.read(info)
            if not allow_identity:
                for pattern in IDENTITY_PATTERNS:
                    if pattern.search(data):
                        identity_hits.append(name)
                        errors.append(f"identity pattern in {name}")
                        break
    return {
        "status": "pass" if not errors else "fail",
        "archive": str(path),
        "members": len(names),
        "uncompressed_bytes": sum(info.file_size for info in infos),
        "required_paths": list(required),
        "identity_hits": sorted(set(identity_hits)),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--required", nargs="*", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-identity", action="store_true")
    args = parser.parse_args()
    report = validate_archive(args.archive, args.required, args.allow_identity)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
