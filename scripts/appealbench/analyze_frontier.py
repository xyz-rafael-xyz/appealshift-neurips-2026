#!/usr/bin/env python3
"""Analyze the matched invalid and valid AppealShift frontier controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


CONDITIONS = ("independent_review", "prior_rationale")
CONVENTIONS = {"printed": "INELIGIBLE", "need_information": "NEED_INFORMATION"}


def load(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invalid", type=Path, required=True)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("experiments/appealbench/frontier_analysis.json"))
    args = parser.parse_args()
    invalid = load(args.invalid)
    valid = load(args.valid)
    result: dict[str, object] = {
        "analysis_kind": "post-audit matched frontier source discrimination",
        "model": sorted({str(row["model"]) for row in invalid + valid}),
        "conventions": CONVENTIONS,
        "conditions": {},
        "run_sha256": {
            str(args.invalid): hashlib.sha256(args.invalid.read_bytes()).hexdigest(),
            str(args.valid): hashlib.sha256(args.valid.read_bytes()).hexdigest(),
        },
    }
    for condition in CONDITIONS:
        bad = [row for row in invalid if row["condition"] == condition]
        good = [row for row in valid if row["condition"] == condition]
        if len(bad) != 96 or len(good) != 48:
            raise SystemExit(f"{condition}: expected 96 invalid and 48 valid rows")
        bad_predictions = [str(row["score"]["disposition"]) for row in bad]
        good_predictions = [str(row["score"]["disposition"]) for row in good]
        valid_exact = sum(value == "ELIGIBLE" for value in good_predictions) / len(good)
        source_specificity = sum(value != "ELIGIBLE" for value in bad_predictions) / len(bad)
        condition_result = {
            "invalid_n": len(bad),
            "valid_n": len(good),
            "invalid_prediction_counts": dict(Counter(bad_predictions)),
            "valid_prediction_counts": dict(Counter(good_predictions)),
            "invalid_source_specificity": source_specificity,
            "valid_source_sensitivity": valid_exact,
            "balanced_source_discrimination": (source_specificity + valid_exact) / 2,
            "strict_schema_rate": sum(bool(row["score"]["strict_format"]) for row in bad + good) / (len(bad) + len(good)),
            "fully_grounded_rate": sum(bool(row["score"]["fully_grounded"]) for row in bad + good) / (len(bad) + len(good)),
            "convention_scores": {},
        }
        for name, target in CONVENTIONS.items():
            invalid_exact = sum(value == target for value in bad_predictions) / len(bad)
            condition_result["convention_scores"][name] = {
                "invalid_target": target,
                "invalid_exact_accuracy": invalid_exact,
                "valid_exact_accuracy": valid_exact,
                "balanced_exact_accuracy": (invalid_exact + valid_exact) / 2,
            }
        result["conditions"][condition] = condition_result
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
