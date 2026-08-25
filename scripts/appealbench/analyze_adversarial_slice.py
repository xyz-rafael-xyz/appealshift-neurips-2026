#!/usr/bin/env python3
"""Summarize the exploratory AppealShift adversarial slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def load_jsonl(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("experiments/appealbench/adversarial_analysis.json")
    )
    args = parser.parse_args()
    rows = load_jsonl(args.runs)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["model"]), str(row["condition"]))].append(row)
    summaries = []
    for (model, condition), records in sorted(groups.items()):
        summaries.append(
            {
                "model": model,
                "condition": condition,
                "n": len(records),
                "disposition_accuracy": mean(
                    int(record["score"]["disposition_correct"]) for record in records
                ),
                "false_eligibility": mean(
                    int(record["score"]["false_eligibility"]) for record in records
                ),
                "fully_grounded": mean(
                    int(record["score"]["fully_grounded"]) for record in records
                ),
            }
        )
    condition_summaries = []
    for condition in ("independent_review", "prior_rationale"):
        selected = [row for row in rows if row["condition"] == condition]
        condition_summaries.append(
            {
                "condition": condition,
                "n": len(selected),
                "disposition_accuracy": mean(
                    int(row["score"]["disposition_correct"]) for row in selected
                ),
                "false_eligibility": mean(
                    int(row["score"]["false_eligibility"]) for row in selected
                ),
            }
        )
    payload = {
        "status": "exploratory_robustness_slice",
        "records": len(rows),
        "semantic_cases": len({row["case_id"] for row in rows}),
        "conditions": condition_summaries,
        "model_conditions": summaries,
        "run_files": [
            {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in args.runs
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
