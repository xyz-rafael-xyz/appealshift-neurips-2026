#!/usr/bin/env python3
"""Create a deterministic score-blind AppealBench audit packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from audit_scorer import audit_score


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}|{label}".encode()).digest()
    return seed + int.from_bytes(digest[:8], "big")


def select_records(
    records: Sequence[Dict[str, object]], per_stratum: int, seed: int
) -> List[Dict[str, object]]:
    strata: Dict[Tuple[str, str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for record in records:
        key = (
            str(record["model"]),
            str(record["condition"]),
            str(record["evidence_state"]),
            str(record["surface_form"]),
        )
        strata[key].append(record)
    selected: List[Dict[str, object]] = []
    for key, values in sorted(strata.items()):
        ordered = sorted(values, key=lambda record: str(record["variant_id"]))
        rng = random.Random(stable_seed(seed, "|".join(key)))
        rng.shuffle(ordered)
        selected.extend(ordered[:per_stratum])
    return sorted(
        selected,
        key=lambda record: (
            str(record["model"]),
            str(record["condition"]),
            str(record["evidence_state"]),
            str(record["surface_form"]),
            str(record["variant_id"]),
        ),
    )


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def build_packet(
    selected: Sequence[Dict[str, object]], cases: Dict[str, Dict[str, object]]
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    packet: List[Dict[str, object]] = []
    answer_key: List[Dict[str, object]] = []
    for index, record in enumerate(selected, start=1):
        audit_id = f"AB-AUD-{index:04d}"
        row = cases[str(record["variant_id"])]
        packet.append(
            {
                "audit_id": audit_id,
                "service_family": row["service_family"],
                "surface_form": row["surface_form"],
                "requested_service": row["requested_service"],
                "request_id": row["request_id"],
                "policy": row["policy"],
                "current_record": row["current_record"],
                "appeal_evidence": row["appeal_evidence"],
                "prior_context_shown": record["condition"] != "independent_review",
                "raw_output": record["raw_output"],
                "preliminary_raw_output": record.get("preliminary_raw_output"),
                "reviewer_fields": {
                    "disposition": None,
                    "policy_clause": None,
                    "evidence_ids": None,
                    "schema_valid": None,
                    "notes": None,
                },
            }
        )
        answer_key.append(
            {
                "audit_id": audit_id,
                "model": record["model"],
                "condition": record["condition"],
                "case_id": record["case_id"],
                "variant_id": record["variant_id"],
                "evidence_state": record["evidence_state"],
                "target_disposition": row["target_disposition"],
                "target_clause": row["target_clause"],
                "target_evidence_ids": row["target_evidence_ids"],
                "independent_audit_score": audit_score(row, str(record["raw_output"])),
            }
        )
    return packet, answer_key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-stratum", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260822)
    args = parser.parse_args()
    rows = load_jsonl(args.dataset)
    cases = {str(row["variant_id"]): row for row in rows}
    records = [record for path in args.runs for record in load_jsonl(path)]
    selected = select_records(records, args.per_stratum, args.seed)
    packet, answer_key = build_packet(selected, cases)
    packet_path = args.output_dir / "audit_packet.jsonl"
    answer_path = args.output_dir / "answer_key.jsonl"
    write_jsonl(packet_path, packet)
    write_jsonl(answer_path, answer_key)
    manifest = {
        "selection_uses_scores": False,
        "seed": args.seed,
        "per_stratum": args.per_stratum,
        "strata": len(
            {
                (
                    record["model"],
                    record["condition"],
                    record["evidence_state"],
                    record["surface_form"],
                )
                for record in records
            }
        ),
        "selected_records": len(selected),
        "source_records": len(records),
        "dataset": str(args.dataset),
        "dataset_sha256": sha256(args.dataset),
        "run_files": [{"path": str(path), "sha256": sha256(path)} for path in args.runs],
        "packet_sha256": sha256(packet_path),
        "answer_key_sha256": sha256(answer_path),
        "human_review_status": "not_performed",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "selection_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
