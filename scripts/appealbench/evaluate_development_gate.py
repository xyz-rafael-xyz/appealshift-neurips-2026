#!/usr/bin/env python3
"""Apply the documented AppealBench version 2 development gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


STATES = ("valid", "invalid", "incomplete", "conflict")
DISPOSITIONS = ("ELIGIBLE", "INELIGIBLE", "NEED_INFORMATION", "HUMAN_REVIEW")


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def evaluate(records: List[Dict[str, object]], validation: Dict[str, object]) -> Dict[str, object]:
    predicted = Counter(record["score"]["disposition"] for record in records)
    parser_modes = Counter(record["score"]["parser_mode"] for record in records)
    correct_by_state = {
        state: sum(
            bool(record["score"]["disposition_correct"])
            for record in records
            if record["evidence_state"] == state
        )
        for state in STATES
    }
    disagreement_count = sum(
        int(run["primary_audit_disagreements"]) for run in validation.get("run_files", [])
    )
    checks = {
        "combined_validation_passed": validation.get("status") == "pass",
        "complete_four_model_grid": len(records) == 256,
        "zero_scorer_disagreements": disagreement_count == 0,
        "all_dispositions_observed": all(predicted[value] > 0 for value in DISPOSITIONS),
        "every_state_has_correct_routes": all(correct_by_state[state] > 0 for state in STATES),
        "unparsed_rate_below_five_percent": parser_modes["unparsed"] / len(records) < 0.05,
    }
    return {
        "decision": "proceed_to_evaluation" if all(checks.values()) else "stop_and_revise",
        "checks": checks,
        "records": len(records),
        "predicted_dispositions": {str(key): value for key, value in sorted(predicted.items(), key=lambda x: str(x[0]))},
        "parser_modes": dict(sorted(parser_modes.items())),
        "unparsed_rate": parser_modes["unparsed"] / len(records),
        "correct_by_state": correct_by_state,
        "primary_audit_disagreements": disagreement_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [record for path in args.runs for record in load_jsonl(path)]
    validation = json.loads(args.validation.read_text(encoding="utf-8"))
    report = evaluate(records, validation)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["decision"] != "proceed_to_evaluation":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
