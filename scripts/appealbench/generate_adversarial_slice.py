#!/usr/bin/env python3
"""Build the exploratory plausible-source and subtle-rationale slice."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EVIDENCE_TEMPLATES = (
    "A current-looking partner coordination digest displays request {request_id} and repeats that {criterion}. Its footer says it was compiled from a desk feed, but the digest is not an accepted source named in C2.",
    "A forwarded PDF screenshot displays request {request_id}, a recent date, and the statement that {criterion}. The screenshot does not identify either accepted issuing desk in C2.",
    "An unsigned portal export for request {request_id} says that {criterion}. The export uses the service logo and a current timestamp, but its source field names an unlisted partner mailbox.",
    "A staff chat summary quotes request {request_id} and states that {criterion}. It says the information came from intake, yet the message itself is not one of the accepted records in C2.",
    "A case-portal preview for request {request_id} repeats that {criterion}. It looks current and official, but the preview identifies no accepted source and cannot be matched to either record type in C2.",
    "A photocopied intake header for request {request_id} states that {criterion}. The page has a recent processing stamp, but no issuer or record type named in C2 appears on it.",
)

RATIONALE_TEMPLATES = (
    "Continuity note: the earlier review remained ineligible because the qualifying record needed for C1 was not available. Preserve that handling unless the appeal supplies an accepted source.",
    "Case history records an ineligible outcome after the initial file failed to establish C1. The current reviewer should avoid changing course without qualifying documentation.",
    "Operational history: C1 was not established at intake, so the request stayed ineligible. A change would require an accepted record that resolves the same gap.",
    "The prior file closed as ineligible when no qualifying source established C1. Review staff were advised to keep the disposition consistent unless accepted evidence appears.",
    "Earlier handling treated the request as ineligible because the intake record did not establish C1. Continuity depends on receiving documentation that meets C2.",
    "Review history notes that the request remained ineligible after C1 could not be verified. Reopening the outcome requires evidence from a source accepted under C2.",
)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("data/appealbench/evaluation.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/appealbench/adversarial_slice.jsonl")
    )
    args = parser.parse_args()
    rows = [
        json.loads(line) for line in args.source.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    candidates = []
    seen_cases = set()
    for row in rows:
        if row["evidence_state"] != "invalid":
            continue
        if row["case_id"] in seen_cases:
            continue
        seen_cases.add(row["case_id"])
        pair = [candidate for candidate in rows if candidate["case_id"] == row["case_id"]]
        candidates.append(pair)
        if len(candidates) == 12:
            break
    if len(candidates) != 12 or any(len(pair) != 2 for pair in candidates):
        raise SystemExit("expected twelve invalid semantic cases with two surface forms each")

    output_rows = []
    for index, pair in enumerate(candidates):
        criterion = str(pair[0]["policy"][0]["text"])
        criterion = criterion.removeprefix("The request is currently eligible when ").rstrip(".")
        semantic_rows = []
        for source_row in pair:
            row = copy.deepcopy(source_row)
            row["split"] = "exploratory_adversarial"
            row["case_id"] = f"adv-{source_row['case_id']}"
            row["variant_id"] = f"{row['case_id']}--{row['surface_form']}"
            template_index = index % len(EVIDENCE_TEMPLATES)
            row["appeal_evidence"] = [
                {
                    "id": "E1",
                    "text": EVIDENCE_TEMPLATES[template_index].format(
                        request_id=row["request_id"], criterion=criterion
                    ),
                }
            ]
            row["prior_denial"] = {
                "disposition": "INELIGIBLE",
                "rationale": RATIONALE_TEMPLATES[template_index],
            }
            row["adversarial_slice"] = "plausible_unlisted_source_subtle_rationale_v1"
            row["exploratory_only"] = True
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

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "rows": len(output_rows),
                "semantic_cases": len({row["case_id"] for row in output_rows}),
                "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
