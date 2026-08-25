#!/usr/bin/env python3
"""Validate the frozen plausible-source v2 construction and balance."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from generate_adversarial_v2 import VARIANT_NAMES, build_rows, load_jsonl


def sha256(file_name: Path) -> str:
    return hashlib.sha256(file_name.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/appealbench/evaluation.jsonl"))
    parser.add_argument("--v1", type=Path, default=Path("data/appealbench/adversarial_slice.jsonl"))
    parser.add_argument("--v2", type=Path, default=Path("data/appealbench/adversarial_v2.jsonl"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = load_jsonl(args.v2)
    expected = build_rows(args.source, args.v1)
    failures: list[str] = []
    checks = 0

    def check(value: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not value:
            failures.append(label)

    check(rows == expected, "exact_deterministic_regeneration")
    check(len(rows) == 96, "row_count_96")
    check(len({str(row["case_id"]) for row in rows}) == 48, "semantic_case_count_48")
    check(len({str(row["variant_id"]) for row in rows}) == 96, "unique_variant_ids")
    check({str(row["source_variant"]) for row in rows} == set(VARIANT_NAMES), "source_variants")
    check(Counter(str(row["source_variant"]) for row in rows) == Counter({name: 24 for name in VARIANT_NAMES}), "source_variant_balance")
    check(Counter(str(row["surface_form"]) for row in rows) == Counter({"policy_first": 48, "record_first": 48}), "surface_balance")
    check({str(row["evidence_state"]) for row in rows} == {"invalid"}, "invalid_targets_only")
    check({str(row["target_disposition"]) for row in rows} == {"INELIGIBLE"}, "target_disposition")
    check({str(row["evaluation_role"]) for row in rows} == {"prospectively_frozen_v2"}, "evaluation_role")
    check({str(row["protocol_commit"]) for row in rows} == {"c4ea98b922f2146fdedde8f09b5180d61633c595"}, "protocol_commit")
    check(not any(bool(row["exploratory_only"]) for row in rows), "confirmatory_flag")

    by_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_case[str(row["case_id"])].append(row)
    for case_id, pair in sorted(by_case.items()):
        check(len(pair) == 2, f"{case_id}_pair_size")
        check({str(row["surface_form"]) for row in pair} == {"policy_first", "record_first"}, f"{case_id}_surfaces")
        check(len({str(row["semantic_sha256"]) for row in pair}) == 1, f"{case_id}_semantic_hash")

    result = {
        "status": "pass" if not failures else "fail",
        "checks_executed": checks,
        "failure_count": len(failures),
        "failure_examples": failures[:20],
        "rows": len(rows),
        "semantic_cases": len(by_case),
        "source_variant_counts": dict(sorted(Counter(str(row["source_variant"]) for row in rows).items())),
        "surface_counts": dict(sorted(Counter(str(row["surface_form"]) for row in rows).items())),
        "sha256": sha256(args.v2),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
