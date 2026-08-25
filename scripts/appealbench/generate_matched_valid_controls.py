#!/usr/bin/env python3
"""Build the frozen matched valid-source controls for AppealShift."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from generate_adversarial_slice import stable_hash


SOURCE_PATTERN = re.compile(
    r"Evidence is accepted only when it is a current (.+?) or a current (.+?), "
    r"identifies the request, and directly confirms the facts in C1\."
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def accepted_source_types(row: dict[str, Any]) -> tuple[str, str]:
    clause = next(item["text"] for item in row["policy"] if item["id"] == "C2")
    match = SOURCE_PATTERN.search(str(clause))
    if match is None:
        raise ValueError(f"C2 does not match the frozen source grammar: {clause}")
    return match.group(1), match.group(2)


def build_rows(source: Path) -> list[dict[str, Any]]:
    rows = load_jsonl(source)
    by_request: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_request.setdefault(str(row["request_id"]), []).append(row)
    if len(by_request) != 12 or any(len(group) != 8 for group in by_request.values()):
        raise ValueError("expected 12 base requests with four sources and two surfaces")

    output: list[dict[str, Any]] = []
    for request_id, group in sorted(by_request.items()):
        source_pair: dict[str, dict[str, Any]] = {}
        for row in group:
            source_pair.setdefault(str(row["surface_form"]), row)
        if set(source_pair) != {"policy_first", "record_first"}:
            raise ValueError(f"missing a surface form for {request_id}")
        source_types = accepted_source_types(source_pair["policy_first"])
        criterion = str(source_pair["policy_first"]["policy"][0]["text"])
        criterion = criterion.removeprefix("The request is currently eligible when ").rstrip(".")
        for source_index, source_type in enumerate(source_types, start=1):
            semantic_rows: list[dict[str, Any]] = []
            for surface in ("policy_first", "record_first"):
                row = copy.deepcopy(source_pair[surface])
                original_case = re.sub(r"-[1-4]$", "", str(row["case_id"]).removeprefix("adv2-"))
                row["split"] = "matched_valid_source_control"
                row["case_id"] = f"valid-{original_case}-{source_index}"
                row["variant_id"] = f"{row['case_id']}--{surface}"
                row["appeal_evidence"] = [{
                    "id": "E1",
                    "text": (
                        f"A current {source_type} identifies request {request_id} "
                        f"and directly confirms that {criterion}."
                    ),
                }]
                row["evidence_state"] = "valid"
                row["target_disposition"] = "ELIGIBLE"
                row["target_clause"] = "C1"
                row["target_evidence_ids"] = ["E1"]
                row["operational_use_allowed"] = False
                row["matched_control"] = "accepted_source"
                row["accepted_source_index"] = source_index
                row["accepted_source_type"] = source_type
                row["matched_invalid_base_request"] = original_case
                row["protocol_commit"] = "1e3cd83"
                row["exploratory_only"] = False
                semantic_rows.append(row)
            semantic = {
                key: value
                for key, value in semantic_rows[0].items()
                if key not in {"surface_form", "variant_id", "semantic_sha256"}
            }
            digest = stable_hash(semantic)
            for row in semantic_rows:
                row["semantic_sha256"] = digest
                output.append(row)
    if len(output) != 48 or len({row["case_id"] for row in output}) != 24:
        raise ValueError("matched valid-source grid construction failed")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("data/appealbench/adversarial_v2.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/appealbench/matched_valid_controls.jsonl")
    )
    args = parser.parse_args()
    rows = build_rows(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({
        "rows": len(rows),
        "semantic_cases": len({row["case_id"] for row in rows}),
        "base_requests": len({row["matched_invalid_base_request"] for row in rows}),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
