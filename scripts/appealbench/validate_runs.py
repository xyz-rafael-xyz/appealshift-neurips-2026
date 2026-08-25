#!/usr/bin/env python3
"""Validate complete AppealBench runs by recomputing prompts and scores."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from audit_scorer import audit_score
from protocol import (
    CONDITIONS,
    PROTOCOL_VERSION,
    final_commit_messages,
    initial_messages,
    prompt_hash,
    score_output,
)


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_score(score: Dict[str, object]) -> Dict[str, object]:
    keys = (
        "parser_mode",
        "schema_valid",
        "strict_format",
        "exact_keys",
        "disposition",
        "policy_clause",
        "evidence_ids",
        "reply",
        "reply_characters",
        "reply_words",
        "unsupported_identifiers",
        "disposition_correct",
        "clause_correct",
        "evidence_correct",
        "fully_grounded",
        "failure_to_correct",
        "false_eligibility",
        "appropriate_information_request",
        "appropriate_human_review",
    )
    return {key: score.get(key) for key in keys}


def expected_models(path: Path) -> Dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["id"]): str(item["revision"]) for item in payload["models"]}


def validate_file(
    path: Path,
    cases: Dict[str, Dict[str, object]],
    dataset_path: Path,
    dataset_hash: str,
    revisions: Dict[str, str],
    conditions: tuple[str, ...] = CONDITIONS,
) -> Dict[str, object]:
    records = load_jsonl(path)
    errors: List[str] = []
    model_ids = {str(record.get("model")) for record in records}
    if len(model_ids) != 1:
        errors.append(f"expected one model, found {sorted(model_ids)}")
    model_id = next(iter(model_ids), "")
    expected_revision = revisions.get(model_id)
    if expected_revision is None:
        errors.append(f"unrecognized model {model_id}")
    expected_keys = {
        (variant_id, condition) for variant_id in cases for condition in conditions
    }
    seen: set[tuple[str, str]] = set()
    primary_audit_disagreements = 0
    for index, record in enumerate(records):
        label = f"record {index}"
        variant_id = str(record.get("variant_id"))
        condition = str(record.get("condition"))
        key = (variant_id, condition)
        if key in seen:
            errors.append(f"duplicate key {key}")
        seen.add(key)
        row = cases.get(variant_id)
        if row is None:
            errors.append(f"{label} has unknown variant {variant_id}")
            continue
        if condition not in conditions:
            errors.append(f"{label} has unknown condition {condition}")
            continue
        if record.get("protocol_version") != PROTOCOL_VERSION:
            errors.append(f"{label} protocol version mismatch")
        if record.get("revision") != expected_revision:
            errors.append(f"{label} revision mismatch")
        if record.get("dataset") != str(dataset_path):
            errors.append(f"{label} dataset path mismatch")
        if record.get("dataset_sha256") != dataset_hash:
            errors.append(f"{label} dataset hash mismatch")
        for field in (
            "case_id",
            "service_family",
            "surface_form",
            "evidence_state",
            "target_disposition",
        ):
            if record.get(field) != row.get(field):
                errors.append(f"{label} {field} mismatch")

        raw = record.get("raw_output")
        if not isinstance(raw, str):
            errors.append(f"{label} final output is not text")
            continue
        preliminary = record.get("preliminary_raw_output")
        if condition == "commit_then_review":
            if not isinstance(preliminary, str):
                errors.append(f"{label} lacks preliminary output")
                continue
            preliminary_messages = initial_messages(row, condition)
            final_messages = final_commit_messages(row, preliminary)
            if record.get("preliminary_prompt_sha256") != prompt_hash(preliminary_messages):
                errors.append(f"{label} preliminary prompt hash mismatch")
            preliminary_score = score_output(row, preliminary)
            if record.get("preliminary_score") != preliminary_score:
                errors.append(f"{label} preliminary stored score mismatch")
            expected_update = {
                "changed_disposition": (
                    preliminary_score["disposition"] != score_output(row, raw)["disposition"]
                ),
                "corrective_update": (
                    not preliminary_score["disposition_correct"]
                    and score_output(row, raw)["disposition_correct"]
                ),
                "harmful_update": (
                    preliminary_score["disposition_correct"]
                    and not score_output(row, raw)["disposition_correct"]
                ),
            }
            if record.get("update") != expected_update:
                errors.append(f"{label} update record mismatch")
        else:
            final_messages = initial_messages(row, condition)
            if preliminary is not None or record.get("preliminary_score") is not None:
                errors.append(f"{label} has unexpected preliminary data")
            if record.get("preliminary_prompt_sha256") is not None:
                errors.append(f"{label} has unexpected preliminary prompt hash")
            if record.get("update") is not None:
                errors.append(f"{label} has unexpected update data")
        if record.get("final_prompt_sha256") != prompt_hash(final_messages):
            errors.append(f"{label} final prompt hash mismatch")
        primary = score_output(row, raw)
        if record.get("score") != primary:
            errors.append(f"{label} stored final score mismatch")
        independent = audit_score(row, raw)
        if canonical_score(primary) != canonical_score(independent):
            primary_audit_disagreements += 1
            errors.append(f"{label} independent score disagreement")

    missing = expected_keys - seen
    extras = seen - expected_keys
    if missing:
        errors.append(f"missing {len(missing)} expected keys")
    if extras:
        errors.append(f"found {len(extras)} unexpected keys")
    balance = Counter((record.get("condition"), record.get("evidence_state")) for record in records)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "model": model_id,
        "revision": expected_revision,
        "records": len(records),
        "expected_records": len(expected_keys),
        "balance": {f"{key[0]}|{key[1]}": value for key, value in sorted(balance.items())},
        "primary_audit_disagreements": primary_audit_disagreements,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--models", type=Path, default=Path("experiments/appealbench/models.json")
    )
    parser.add_argument(
        "--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS)
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = load_jsonl(args.dataset)
    cases = {str(row["variant_id"]): row for row in rows}
    dataset_hash = sha256(args.dataset)
    revisions = expected_models(args.models)
    reports = [
        validate_file(
            path, cases, args.dataset, dataset_hash, revisions, tuple(args.conditions)
        )
        for path in args.runs
    ]
    errors = [f"{report['path']} | {error}" for report in reports for error in report["errors"]]
    reported_models = [report["model"] for report in reports]
    if len(reported_models) != len(set(reported_models)):
        errors.append("duplicate model run files")
    report = {
        "status": "pass" if not errors else "fail",
        "dataset": str(args.dataset),
        "dataset_sha256": dataset_hash,
        "dataset_rows": len(rows),
        "run_files": reports,
        "errors": errors,
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
