#!/usr/bin/env python3
"""Score frozen AppealShift outputs under two invalid-appeal conventions."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


CONDITIONS = ("independent_review", "prior_rationale")
CONVENTIONS = {"printed": "INELIGIBLE", "need_information": "NEED_INFORMATION"}


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def short_model(path: Path) -> str:
    return path.stem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invalid-dir", type=Path, default=Path("experiments/appealbench/adversarial_v2"))
    parser.add_argument("--valid-dir", type=Path, default=Path("experiments/appealbench/matched_valid_controls"))
    parser.add_argument("--output", type=Path, default=Path("experiments/appealbench/dual_convention_analysis.json"))
    args = parser.parse_args()

    invalid_paths = sorted(args.invalid_dir.glob("*.jsonl"))
    valid_paths = sorted(args.valid_dir.glob("*.jsonl"))
    if {path.stem for path in invalid_paths} != {path.stem for path in valid_paths}:
        raise SystemExit("invalid and valid model sets differ")
    result: dict[str, object] = {
        "analysis_kind": "deterministic post-audit dual-convention scoring",
        "conventions": CONVENTIONS,
        "models": {},
        "run_sha256": {},
    }
    for invalid_path in invalid_paths:
        model = short_model(invalid_path)
        valid_path = args.valid_dir / invalid_path.name
        invalid = [row for row in load_jsonl(invalid_path) if row.get("record_type") == "appeal_review"]
        valid = [row for row in load_jsonl(valid_path) if row.get("record_type") == "appeal_review"]
        result["run_sha256"][str(invalid_path)] = hashlib.sha256(invalid_path.read_bytes()).hexdigest()
        result["run_sha256"][str(valid_path)] = hashlib.sha256(valid_path.read_bytes()).hexdigest()
        model_result = {}
        for condition in CONDITIONS:
            bad = [row for row in invalid if row.get("condition") == condition]
            good = [row for row in valid if row.get("condition") == condition]
            if len(bad) != 96 or len(good) != 48:
                raise SystemExit(f"{model} {condition}: expected 96 invalid and 48 valid rows")
            predicted_good = [str((row.get("score") or {}).get("disposition")) for row in good]
            predicted_bad = [str((row.get("score") or {}).get("disposition")) for row in bad]
            valid_exact = sum(value == "ELIGIBLE" for value in predicted_good) / len(good)
            convention_rows = {}
            for name, invalid_target in CONVENTIONS.items():
                invalid_exact = sum(value == invalid_target for value in predicted_bad) / len(bad)
                convention_rows[name] = {
                    "invalid_target": invalid_target,
                    "invalid_n": len(bad),
                    "invalid_exact_accuracy": invalid_exact,
                    "valid_target": "ELIGIBLE",
                    "valid_n": len(good),
                    "valid_exact_accuracy": valid_exact,
                    "balanced_exact_accuracy": (invalid_exact + valid_exact) / 2,
                }
            model_result[condition] = {
                "invalid_prediction_counts": dict(Counter(predicted_bad)),
                "valid_prediction_counts": dict(Counter(predicted_good)),
                "scores": convention_rows,
            }
        result["models"][model] = model_result
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
