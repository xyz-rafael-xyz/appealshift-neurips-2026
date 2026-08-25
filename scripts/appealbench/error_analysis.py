#!/usr/bin/env python3
"""Produce deterministic AppealBench confusion and paired-failure tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Sequence


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def confusion_rows(records: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    counts = Counter(
        (
            str(record["model"]),
            str(record["condition"]),
            str(record["target_disposition"]),
            str(record["score"]["disposition"]),
        )
        for record in records
    )
    return [
        {
            "model": model,
            "condition": condition,
            "target": target,
            "predicted": predicted,
            "count": count,
        }
        for (model, condition, target, predicted), count in sorted(counts.items())
    ]


def paired_failures(records: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    cells: Dict[tuple[str, str, str], Dict[str, object]] = {}
    for record in records:
        cells[(str(record["model"]), str(record["variant_id"]), str(record["condition"]))] = record
    output: List[Dict[str, object]] = []
    for (model, variant, condition), independent in sorted(cells.items()):
        if condition != "independent_review":
            continue
        for comparison in ("prior_rationale", "evidence_checklist", "commit_then_review"):
            other = cells.get((model, variant, comparison))
            if other is None:
                continue
            independent_correct = bool(independent["score"]["disposition_correct"])
            other_correct = bool(other["score"]["disposition_correct"])
            if independent_correct == other_correct and (
                independent["score"]["disposition"] == other["score"]["disposition"]
            ):
                continue
            output.append(
                {
                    "model": model,
                    "case_id": independent["case_id"],
                    "variant_id": variant,
                    "evidence_state": independent["evidence_state"],
                    "surface_form": independent["surface_form"],
                    "comparison": comparison,
                    "independent_disposition": independent["score"]["disposition"],
                    "comparison_disposition": other["score"]["disposition"],
                    "independent_correct": independent_correct,
                    "comparison_correct": other_correct,
                    "change_kind": (
                        "corrective"
                        if not independent_correct and other_correct
                        else "harmful"
                        if independent_correct and not other_correct
                        else "different_same_correctness"
                    ),
                }
            )
    return output


def surface_disagreements(records: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    cells: Dict[tuple[str, str, str], Dict[str, object]] = {}
    for record in records:
        cells[(str(record["model"]), str(record["case_id"]), str(record["condition"]))] = cells.get(
            (str(record["model"]), str(record["case_id"]), str(record["condition"])), {}
        )
        cells[(str(record["model"]), str(record["case_id"]), str(record["condition"]))][
            str(record["surface_form"])
        ] = record
    output = []
    for (model, case_id, condition), pair in sorted(cells.items()):
        policy = pair.get("policy_first")
        record = pair.get("record_first")
        if policy is None or record is None:
            continue
        if policy["score"]["disposition"] == record["score"]["disposition"]:
            continue
        output.append(
            {
                "model": model,
                "case_id": case_id,
                "condition": condition,
                "evidence_state": policy["evidence_state"],
                "policy_first_disposition": policy["score"]["disposition"],
                "record_first_disposition": record["score"]["disposition"],
                "policy_first_correct": policy["score"]["disposition_correct"],
                "record_first_correct": record["score"]["disposition_correct"],
            }
        )
    return output


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    records = [record for path in args.runs for record in load_jsonl(path)]
    confusion = confusion_rows(records)
    paired = paired_failures(records)
    surfaces = surface_disagreements(records)
    write_csv(args.output_dir / "confusion.csv", confusion)
    write_csv(args.output_dir / "paired_changes.csv", paired)
    write_csv(args.output_dir / "surface_disagreements.csv", surfaces)
    manifest = {
        "records": len(records),
        "confusion_rows": len(confusion),
        "paired_change_rows": len(paired),
        "surface_disagreement_rows": len(surfaces),
        "run_files": [{"path": str(path), "sha256": sha256(path)} for path in args.runs],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
