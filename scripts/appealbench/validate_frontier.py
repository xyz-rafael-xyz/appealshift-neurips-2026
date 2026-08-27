#!/usr/bin/env python3
"""Validate the AppealShift matched frontier controls and analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invalid", type=Path, default=Path("experiments/appealbench/frontier/gpt-5-6-sol-invalid.jsonl"))
    parser.add_argument("--valid", type=Path, default=Path("experiments/appealbench/frontier/gpt-5-6-sol-valid.jsonl"))
    parser.add_argument("--analysis", type=Path, default=Path("experiments/appealbench/frontier_analysis.json"))
    parser.add_argument("--output", type=Path, default=Path("validation/appealbench/frontier_validation.json"))
    args = parser.parse_args()
    invalid = load(args.invalid)
    valid = load(args.valid)
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    rows = invalid + valid
    cells = {(str(row.get("condition")), str(row.get("evidence_state"))) for row in rows}
    checks = {
        "record_counts": len(invalid) == 192 and len(valid) == 96,
        "unique_cells": len({(str(row.get("variant_id")), str(row.get("condition"))) for row in invalid}) == 192 and len({(str(row.get("variant_id")), str(row.get("condition"))) for row in valid}) == 96,
        "condition_state_grid": cells == {("independent_review", "invalid"), ("prior_rationale", "invalid"), ("independent_review", "valid"), ("prior_rationale", "valid")},
        "model_exact": {str(row.get("model")) for row in rows} == {"openai/gpt-5.6-sol"},
        "provider_openai": all((row.get("response_trace") or {}).get("provider") == "OpenAI" for row in rows),
        "strict_and_grounded": all(bool(row["score"]["strict_format"]) and bool(row["score"]["fully_grounded"]) for row in rows),
        "invalid_dispositions": {str(row["score"]["disposition"]) for row in invalid} == {"INELIGIBLE"},
        "valid_dispositions": {str(row["score"]["disposition"]) for row in valid} == {"ELIGIBLE"},
        "analysis_exact": all(
            cell.get("balanced_source_discrimination") == 1.0
            and cell.get("convention_scores", {}).get("printed", {}).get("balanced_exact_accuracy") == 1.0
            and cell.get("convention_scores", {}).get("need_information", {}).get("balanced_exact_accuracy") == 0.5
            for cell in analysis.get("conditions", {}).values()
        ) and len(analysis.get("conditions", {})) == 2,
    }
    report = {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "invalid_sha256": hashlib.sha256(args.invalid.read_bytes()).hexdigest(),
        "valid_sha256": hashlib.sha256(args.valid.read_bytes()).hexdigest(),
        "analysis_sha256": hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
        "recorded_cost_usd": sum(float(row.get("cost_usd") or 0.0) for row in rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
