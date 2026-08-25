#!/usr/bin/env python3
"""Bind AppealBench inputs, code, and completed model runs by hash."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def describe(path: Path) -> Dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def describe_run(path: Path) -> Dict[str, object]:
    rows = load_jsonl(path)
    models = sorted({str(row.get("model")) for row in rows})
    revisions = sorted({str(row.get("revision")) for row in rows})
    protocols = sorted({str(row.get("protocol_version")) for row in rows})
    dataset_hashes = sorted({str(row.get("dataset_sha256")) for row in rows})
    return {
        **describe(path),
        "records": len(rows),
        "models": models,
        "revisions": revisions,
        "protocol_versions": protocols,
        "dataset_hashes": dataset_hashes,
    }


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_manifest(
    dataset: Path,
    models: Path,
    code: Iterable[Path],
    runs: Iterable[Path],
    evidence: Iterable[Path],
) -> Dict[str, object]:
    run_items = [describe_run(path) for path in runs]
    return {
        "git_head": git_head(),
        "dataset": describe(dataset),
        "models": describe(models),
        "code": [describe(path) for path in code],
        "runs": run_items,
        "evidence": [describe(path) for path in evidence],
        "total_run_records": sum(int(item["records"]) for item in run_items),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--code", type=Path, nargs="+", required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--evidence", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_manifest(args.dataset, args.models, args.code, args.runs, args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
