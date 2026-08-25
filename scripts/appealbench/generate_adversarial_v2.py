#!/usr/bin/env python3
"""Build the prospectively frozen AppealShift plausible-source v2 set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_adversarial_slice import EVIDENCE_TEMPLATES, RATIONALE_TEMPLATES, stable_hash


VARIANT_NAMES = ("coordination_digest", "forwarded_screenshot", "portal_export", "staff_chat")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_rows(source: Path, v1: Path) -> list[dict[str, Any]]:
    """Return the frozen v2 rows without reading or mutating the output file."""
    rows = load_jsonl(source)
    v1_base_ids = {str(row["case_id"]).removeprefix("adv-") for row in load_jsonl(v1)}
    invalid_by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["evidence_state"] == "invalid":
            invalid_by_case.setdefault(str(row["case_id"]), []).append(row)
    unused = [pair for case_id, pair in invalid_by_case.items() if case_id not in v1_base_ids]
    if len(unused) != 12 or any(len(pair) != 2 for pair in unused):
        raise SystemExit("v2 requires 12 unused invalid cases with two surface forms each")

    output_rows: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(unused):
        criterion = str(pair[0]["policy"][0]["text"])
        criterion = criterion.removeprefix("The request is currently eligible when ").rstrip(".")
        for variant_index, variant_name in enumerate(VARIANT_NAMES):
            semantic_rows = []
            for source_row in pair:
                row = copy.deepcopy(source_row)
                row["split"] = "prospective_adversarial_v2"
                row["case_id"] = f"adv2-{source_row['case_id']}-{variant_index + 1}"
                row["variant_id"] = f"{row['case_id']}--{row['surface_form']}"
                row["appeal_evidence"] = [{
                    "id": "E1",
                    "text": EVIDENCE_TEMPLATES[variant_index].format(
                        request_id=row["request_id"], criterion=criterion
                    ),
                }]
                rationale_index = (pair_index + variant_index) % len(RATIONALE_TEMPLATES)
                row["prior_denial"] = {
                    "disposition": "INELIGIBLE",
                    "rationale": RATIONALE_TEMPLATES[rationale_index],
                }
                row["adversarial_slice"] = "plausible_unlisted_source_v2"
                row["source_variant"] = variant_name
                row["evaluation_role"] = "prospectively_frozen_v2"
                row["protocol_commit"] = "c4ea98b922f2146fdedde8f09b5180d61633c595"
                row["exploratory_only"] = False
                semantic_rows.append(row)
            semantic = {
                key: value
                for key, value in semantic_rows[0].items()
                if key not in {"surface_form", "variant_id", "semantic_sha256"}
            }
            semantic_digest = stable_hash(semantic)
            for row in semantic_rows:
                row["semantic_sha256"] = semantic_digest
                output_rows.append(row)

    semantic_cases = {str(row["case_id"]) for row in output_rows}
    if len(output_rows) != 96 or len(semantic_cases) != 48:
        raise SystemExit("v2 grid construction failed")
    return output_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/appealbench/evaluation.jsonl"))
    parser.add_argument("--v1", type=Path, default=Path("data/appealbench/adversarial_slice.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/appealbench/adversarial_v2.jsonl"))
    args = parser.parse_args()
    output_rows = build_rows(args.source, args.v1)
    semantic_cases = {str(row["case_id"]) for row in output_rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    print(json.dumps({
        "rows": len(output_rows),
        "semantic_cases": len(semantic_cases),
        "base_cases": 12,
        "source_variants": list(VARIANT_NAMES),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
