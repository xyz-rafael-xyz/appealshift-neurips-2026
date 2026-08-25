#!/usr/bin/env python3
"""Build deterministic AppealShift archives from explicit repository paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


SKIP_PARTS = {"__pycache__", ".DS_Store"}
FIXED_TIME = (2026, 8, 22, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(root: Path, includes: Sequence[Path]) -> List[Tuple[Path, str]]:
    root = root.resolve()
    files: Dict[str, Path] = {}
    for relative in includes:
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"include must be a safe relative path, got {relative}")
        source = root / relative
        if not source.exists():
            raise FileNotFoundError(source)
        candidates: Iterable[Path] = source.rglob("*") if source.is_dir() else [source]
        for candidate in candidates:
            if candidate.is_dir() or any(part in SKIP_PARTS for part in candidate.parts):
                continue
            if candidate.is_symlink():
                raise ValueError(f"symbolic links are not allowed, got {candidate}")
            resolved = candidate.resolve()
            try:
                archive_name = resolved.relative_to(root).as_posix()
            except ValueError as error:
                raise ValueError(f"path escapes root, got {candidate}") from error
            files[archive_name] = resolved
    return [(files[name], name) for name in sorted(files)]


def build(root: Path, output: Path, includes: Sequence[Path]) -> Dict[str, object]:
    files = collect(root, includes)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True
    ) as archive:
        for source, name in files:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o100755 if source.stat().st_mode & 0o111 else 0o100644
            info.external_attr = mode << 16
            info.create_system = 3
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {
        "archive": str(output),
        "sha256": sha256(output),
        "members": len(files),
        "files": [
            {"path": name, "bytes": source.stat().st_size, "sha256": sha256(source)}
            for source, name in files
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include", type=Path, nargs="+", required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    report = build(args.root, args.output, args.include)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
