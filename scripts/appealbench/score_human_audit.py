#!/usr/bin/env python3
"""Score a completed human audit against the hidden AppealShift answer key."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def evidence_set(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return tuple(sorted(value))


def cohen_kappa(left: Sequence[object], right: Sequence[object]) -> float | None:
    if len(left) != len(right) or not left:
        return None
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum(
        left_counts[label] / len(left) * right_counts[label] / len(right)
        for label in set(left_counts) | set(right_counts)
    )
    if expected == 1:
        return 1.0 if observed == 1 else None
    return (observed - expected) / (1 - expected)


def compare(
    packet: Iterable[Dict[str, object]], answer_key: Iterable[Dict[str, object]]
) -> Dict[str, object]:
    packet_by_id = {str(row["audit_id"]): row for row in packet}
    key_by_id = {str(row["audit_id"]): row for row in answer_key}
    if set(packet_by_id) != set(key_by_id):
        raise ValueError("audit identifiers do not match")
    fields = ("disposition", "policy_clause", "evidence_ids", "schema_valid")
    agreements = Counter()
    labels: Dict[str, List[object]] = {field: [] for field in fields}
    targets: Dict[str, List[object]] = {field: [] for field in fields}
    disagreements = []
    for audit_id in sorted(packet_by_id):
        reviewer = packet_by_id[audit_id].get("reviewer_fields")
        if not isinstance(reviewer, dict):
            raise ValueError(f"{audit_id} lacks reviewer_fields")
        if any(reviewer.get(field) is None for field in fields):
            raise ValueError(f"{audit_id} has incomplete reviewer fields")
        score = key_by_id[audit_id]["independent_audit_score"]
        observed = {
            "disposition": (
                None if reviewer["disposition"] == "UNPARSEABLE" else reviewer["disposition"]
            ),
            "policy_clause": None if reviewer["policy_clause"] == "" else reviewer["policy_clause"],
            "evidence_ids": evidence_set(reviewer["evidence_ids"]),
            "schema_valid": reviewer["schema_valid"],
        }
        expected = {
            "disposition": score["disposition"],
            "policy_clause": score["policy_clause"],
            "evidence_ids": evidence_set(score["evidence_ids"]),
            "schema_valid": score["schema_valid"],
        }
        row_differences = []
        for field in fields:
            labels[field].append(observed[field])
            targets[field].append(expected[field])
            if observed[field] == expected[field]:
                agreements[field] += 1
            else:
                row_differences.append(field)
        if row_differences:
            disagreements.append({"audit_id": audit_id, "fields": row_differences})
    total = len(packet_by_id)
    return {
        "status": "complete",
        "records": total,
        "agreement": {field: agreements[field] / total for field in fields},
        "kappa": {field: cohen_kappa(labels[field], targets[field]) for field in fields},
        "disagreements": disagreements,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(load_jsonl(args.packet), load_jsonl(args.answer_key))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
