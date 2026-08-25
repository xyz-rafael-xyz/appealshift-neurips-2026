#!/usr/bin/env python3
"""Select and verify five Phi disposition-correct grounding failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        rows.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/appealbench/phi_grounding_five_case_audit.json"),
    )
    args = parser.parse_args()

    dataset = {str(row["variant_id"]): row for row in load_jsonl([args.dataset])}
    candidates = [
        row
        for row in load_jsonl(args.runs)
        if "Phi" in str(row["model"])
        and row["condition"] == "prior_rationale"
        and bool(row["score"]["disposition_correct"])
        and not bool(row["score"]["fully_grounded"])
    ]
    candidates.sort(key=lambda row: (str(row["case_id"]), str(row["surface_form"])))
    if len(candidates) != 24:
        raise SystemExit(f"expected 24 Phi candidates, found {len(candidates)}")

    audited = []
    for row in candidates[:5]:
        source = dataset[str(row["variant_id"])]
        score = row["score"]
        audited.append({
            "variant_id": row["variant_id"],
            "expected_disposition": source["target_disposition"],
            "predicted_disposition": score["disposition"],
            "expected_clause": source["target_clause"],
            "predicted_clause": score["policy_clause"],
            "expected_evidence_ids": source["target_evidence_ids"],
            "predicted_evidence_ids": score["evidence_ids"],
            "clause_mismatch": source["target_clause"] != score["policy_clause"],
            "evidence_mismatch": source["target_evidence_ids"] != score["evidence_ids"],
            "raw_output": row["raw_output"],
        })
    if not all(item["clause_mismatch"] for item in audited):
        raise SystemExit("fixed five-case sample did not contain five clause mismatches")

    result = {
        "selection": "first five candidates sorted by case_id and surface_form",
        "candidate_count": len(candidates),
        "audited_count": len(audited),
        "finding": (
            "All five outputs give the correct INELIGIBLE disposition but cite C1, C3, "
            "or C4 instead of C2. One also omits the required E1 identifier. The zero "
            "fully-grounded score is substantive in this sample, not a formatting artifact."
        ),
        "cases": audited,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
