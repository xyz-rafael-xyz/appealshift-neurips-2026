#!/usr/bin/env python3
"""Validate AppealBench balance, pairing, targets, and frozen generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from generate_dataset import (
    EVIDENCE_STATES,
    SERVICE_SPECS,
    SURFACE_FORMS,
    TARGET_CLAUSES,
    TARGETS,
    development_rows,
    evaluation_rows,
    stable_hash,
)


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_lines(rows: List[Dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n").encode()
        for row in rows
    )


def validate_rows(
    rows: List[Dict[str, object]], expected: List[Dict[str, object]], split: str
) -> List[str]:
    errors: List[str] = []
    if rows != expected:
        errors.append(f"{split} file differs from deterministic generator output")
    expected_count = 192 if split == "evaluation" else 16
    if len(rows) != expected_count:
        errors.append(f"{split} row count {len(rows)} != {expected_count}")
    variant_ids = [str(row.get("variant_id")) for row in rows]
    if len(variant_ids) != len(set(variant_ids)):
        errors.append(f"{split} has duplicate variant identifiers")
    if any(row.get("split") != split for row in rows):
        errors.append(f"{split} contains a wrong split label")

    known_services = {spec["slug"] for spec in SERVICE_SPECS}
    for row in rows:
        label = str(row.get("variant_id"))
        if row.get("service_family") not in known_services:
            errors.append(f"{label} has an unknown service family")
        state = str(row.get("evidence_state"))
        if state not in EVIDENCE_STATES:
            errors.append(f"{label} has an unknown evidence state")
            continue
        if row.get("target_disposition") != TARGETS[state]:
            errors.append(f"{label} target disposition is inconsistent")
        if row.get("target_clause") != TARGET_CLAUSES[state]:
            errors.append(f"{label} target clause is inconsistent")
        if row.get("synthetic") is not True or row.get("operational_use_allowed") is not False:
            errors.append(f"{label} safety flags are invalid")
        if [item.get("id") for item in row.get("policy", [])] != ["C1", "C2", "C3", "C4"]:
            errors.append(f"{label} policy identifiers are invalid")
        evidence_ids = [item.get("id") for item in row.get("appeal_evidence", [])]
        expected_ids = ["E1", "E2"] if state == "conflict" else ["E1"]
        if evidence_ids != expected_ids:
            errors.append(f"{label} evidence identifiers are invalid")
        if row.get("target_evidence_ids") != expected_ids:
            errors.append(f"{label} target evidence set is invalid")
        if row.get("prior_denial", {}).get("disposition") != "INELIGIBLE":
            errors.append(f"{label} prior disposition is invalid")
        semantic = {
            key: value
            for key, value in row.items()
            if key not in {"surface_form", "variant_id", "semantic_sha256"}
        }
        if row.get("semantic_sha256") != stable_hash(semantic):
            errors.append(f"{label} semantic hash mismatch")

    by_case: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_case[str(row["case_id"])].append(row)
    if split == "evaluation":
        if len(by_case) != 96:
            errors.append(f"evaluation base case count {len(by_case)} != 96")
        for case_id, variants in by_case.items():
            if {row["surface_form"] for row in variants} != set(SURFACE_FORMS):
                errors.append(f"{case_id} is missing a surface form")
            if len({row["semantic_sha256"] for row in variants}) != 1:
                errors.append(f"{case_id} variants differ semantically")
        service_state = Counter(
            (rows_for_case[0]["service_family"], rows_for_case[0]["evidence_state"])
            for rows_for_case in by_case.values()
        )
        for service in known_services:
            for state in EVIDENCE_STATES:
                if service_state[(service, state)] != 3:
                    errors.append(f"{service}/{state} base count is not 3")
        if Counter(row["target_disposition"] for row in rows) != Counter(
            {target: 48 for target in TARGETS.values()}
        ):
            errors.append("evaluation target rows are not balanced")
    else:
        if len(by_case) != 16:
            errors.append(f"development base case count {len(by_case)} != 16")
        if Counter(row["target_disposition"] for row in rows) != Counter(
            {target: 4 for target in TARGETS.values()}
        ):
            errors.append("development target rows are not balanced")
        if Counter(row["service_family"] for row in rows) != Counter(
            {service: 2 for service in known_services}
        ):
            errors.append("development service rows are not balanced")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evaluation", type=Path, default=Path("data/appealbench/evaluation.jsonl")
    )
    parser.add_argument(
        "--development", type=Path, default=Path("data/appealbench/development.jsonl")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    eval_rows = load_jsonl(args.evaluation)
    dev_rows = load_jsonl(args.development)
    errors = validate_rows(eval_rows, evaluation_rows(), "evaluation")
    errors.extend(validate_rows(dev_rows, development_rows(), "development"))
    cross_overlap = set(row["request_id"] for row in eval_rows) & set(
        row["request_id"] for row in dev_rows
    )
    if cross_overlap:
        errors.append("development and evaluation request identifiers overlap")
    report = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "evaluation": {
            "path": str(args.evaluation),
            "sha256": file_sha256(args.evaluation),
            "rows": len(eval_rows),
            "base_cases": len({row["case_id"] for row in eval_rows}),
        },
        "development": {
            "path": str(args.development),
            "sha256": file_sha256(args.development),
            "rows": len(dev_rows),
            "base_cases": len({row["case_id"] for row in dev_rows}),
        },
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
