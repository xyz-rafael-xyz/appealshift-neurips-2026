#!/usr/bin/env python3
"""Compare AppealShift BF16 runs with the same models' four-bit records."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


FAMILIES = {
    "mlx-community/Qwen3-4B-Instruct-2507-4bit": ("Qwen3-4B", "4bit"),
    "mlx-community/Qwen3-4B-Instruct-2507-bf16": ("Qwen3-4B", "bf16"),
    "mlx-community/gemma-3-text-4b-it-4bit": ("Gemma-3-4B", "4bit"),
    "mlx-community/gemma-3-4b-it-bf16": ("Gemma-3-4B", "bf16"),
}


def load(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--four-bit", nargs="+", type=Path, required=True)
    parser.add_argument("--bf16", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("experiments/appealbench/bf16_analysis.json")
    )
    args = parser.parse_args()
    selected = []
    for row in load(args.four_bit):
        if (
            row["model"] in FAMILIES
            and FAMILIES[row["model"]][1] == "4bit"
            and row["evidence_state"] == "valid"
            and row["condition"] in {"independent_review", "prior_rationale"}
        ):
            selected.append(row)
    selected.extend(load(args.bf16))
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        family, precision = FAMILIES[str(row["model"])]
        groups[(family, precision, str(row["condition"]))].append(row)
    summaries = []
    for (family, precision, condition), rows in sorted(groups.items()):
        summaries.append(
            {
                "family": family,
                "precision": precision,
                "condition": condition,
                "n": len(rows),
                "disposition_accuracy": mean(
                    int(row["score"]["disposition_correct"]) for row in rows
                ),
                "fully_grounded": mean(int(row["score"]["fully_grounded"]) for row in rows),
                "schema_valid": mean(int(row["score"]["schema_valid"]) for row in rows),
            }
        )
    contrasts = []
    lookup = {(row["family"], row["precision"], row["condition"]): row for row in summaries}
    for family in sorted({row["family"] for row in summaries}):
        for precision in ("4bit", "bf16"):
            left = lookup[(family, precision, "independent_review")]
            right = lookup[(family, precision, "prior_rationale")]
            contrasts.append(
                {
                    "family": family,
                    "precision": precision,
                    "rationale_minus_independent": (
                        right["disposition_accuracy"] - left["disposition_accuracy"]
                    ),
                }
            )
    payload = {
        "status": "same_model_precision_replication",
        "records": len(selected),
        "summaries": summaries,
        "contrasts": contrasts,
        "source_hashes": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [*args.four_bit, *args.bf16]
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
