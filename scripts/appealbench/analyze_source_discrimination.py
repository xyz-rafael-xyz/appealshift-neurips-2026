#!/usr/bin/env python3
"""Joint analysis of AppealShift invalid and matched valid sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SEED = 20260825
RESAMPLES = 20_000
DISPOSITIONS = ("ELIGIBLE", "INELIGIBLE", "NEED_INFORMATION", "HUMAN_REVIEW", "UNPARSED")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def short_model(model: str) -> str:
    return {
        "mlx-community/Qwen3-4B-Instruct-2507-4bit": "Qwen3-4B",
        "mlx-community/Mistral-7B-Instruct-v0.3-4bit": "Mistral-7B",
        "mlx-community/Phi-4-mini-instruct-mlx-4Bit": "Phi-4-mini",
        "mlx-community/gemma-3-text-4b-it-4bit": "Gemma-3-4B",
    }.get(model, model)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def flatten(records: list[dict[str, Any]], source_class: str) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        score = record["score"]
        predicted = score.get("disposition") or "UNPARSED"
        rows.append({
            "source_class": source_class,
            "model": short_model(str(record["model"])),
            "condition": str(record["condition"]),
            "case_id": str(record["case_id"]),
            "surface_form": str(record["surface_form"]),
            "target": str(record["target_disposition"]),
            "predicted": str(predicted),
            "disposition_correct": int(bool(score["disposition_correct"])),
            "false_eligibility": int(bool(score["false_eligibility"])),
            "fully_grounded": int(bool(score["fully_grounded"])),
        })
    return rows


def invalid_base(case_id: str) -> str:
    value = case_id.removeprefix("adv2-")
    return re.sub(r"-[1-4]$", "", value)


def clustered_invalid_effect(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    for row in rows:
        key = (str(row["model"]), str(row["case_id"]), str(row["surface_form"]))
        pairs[key][str(row["condition"])] = int(row["false_eligibility"])
    effects_by_base: dict[str, list[int]] = defaultdict(list)
    for (model, case_id, surface), pair in pairs.items():
        if {"independent_review", "prior_rationale"} <= set(pair):
            effects_by_base[invalid_base(case_id)].append(
                pair["prior_rationale"] - pair["independent_review"]
            )
    base_effects = {key: statistics.fmean(values) for key, values in sorted(effects_by_base.items())}
    if len(base_effects) != 12 or any(len(effects_by_base[key]) != 32 for key in effects_by_base):
        raise ValueError("expected 12 base clusters with 32 model-source-surface effects each")
    values = list(base_effects.values())
    rng = random.Random(SEED)
    boot = [statistics.fmean(rng.choice(values) for _ in range(12)) for _ in range(RESAMPLES)]
    return {
        "n_base_request_clusters": 12,
        "effects_per_cluster": 32,
        "prior_minus_independent": statistics.fmean(values),
        "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "seed": SEED,
        "resamples": RESAMPLES,
        "base_request_effects": base_effects,
    }


def clustered_invalid_effect_by_semantic_case(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reproduce the 48-case clustering unit named in the 24 August protocol."""
    pairs: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    for row in rows:
        key = (str(row["model"]), str(row["case_id"]), str(row["surface_form"]))
        pairs[key][str(row["condition"])] = int(row["false_eligibility"])
    effects_by_case: dict[str, list[int]] = defaultdict(list)
    for (model, case_id, surface), pair in pairs.items():
        if {"independent_review", "prior_rationale"} <= set(pair):
            effects_by_case[case_id].append(
                pair["prior_rationale"] - pair["independent_review"]
            )
    case_effects = {key: statistics.fmean(values) for key, values in sorted(effects_by_case.items())}
    if len(case_effects) != 48 or any(len(effects_by_case[key]) != 8 for key in effects_by_case):
        raise ValueError("expected 48 semantic-case clusters with 8 model-surface effects each")
    values = list(case_effects.values())
    rng = random.Random(SEED)
    boot = [statistics.fmean(rng.choice(values) for _ in range(48)) for _ in range(RESAMPLES)]
    return {
        "n_semantic_case_clusters": 48,
        "effects_per_cluster": 8,
        "prior_minus_independent": statistics.fmean(values),
        "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "seed": SEED,
        "resamples": RESAMPLES,
        "semantic_case_effects": case_effects,
    }


def joint_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["model"]), str(row["condition"]))].append(row)
    output = []
    for (model, condition), group in sorted(groups.items()):
        valid = [row for row in group if row["source_class"] == "matched_valid"]
        invalid = [row for row in group if row["source_class"] == "plausible_unlisted"]
        output.append({
            "model": model,
            "condition": condition,
            "valid_n": len(valid),
            "valid_sensitivity": statistics.fmean(row["predicted"] == "ELIGIBLE" for row in valid),
            "valid_exact_accuracy": statistics.fmean(row["disposition_correct"] for row in valid),
            "invalid_n": len(invalid),
            "invalid_specificity": statistics.fmean(row["predicted"] != "ELIGIBLE" for row in invalid),
            "invalid_exact_accuracy": statistics.fmean(row["disposition_correct"] for row in invalid),
            "balanced_source_discrimination": statistics.fmean([
                statistics.fmean(row["predicted"] == "ELIGIBLE" for row in valid),
                statistics.fmean(row["predicted"] != "ELIGIBLE" for row in invalid),
            ]),
        })
    return output


def confusion(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        (row["model"], row["condition"], row["source_class"], row["target"], row["predicted"])
        for row in rows
    )
    output = []
    for model in sorted({row["model"] for row in rows}):
        for condition in sorted({row["condition"] for row in rows}):
            for source_class, target in (("matched_valid", "ELIGIBLE"), ("plausible_unlisted", "INELIGIBLE")):
                for predicted in DISPOSITIONS:
                    output.append({
                        "model": model,
                        "condition": condition,
                        "source_class": source_class,
                        "target": target,
                        "predicted": predicted,
                        "count": counts[(model, condition, source_class, target, predicted)],
                    })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invalid-runs", type=Path, nargs="+", required=True)
    parser.add_argument("--valid-runs", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("experiments/appealbench/source_discrimination_analysis.json")
    )
    args = parser.parse_args()
    invalid_records = [row for path in args.invalid_runs for row in load_jsonl(path)]
    valid_records = [row for path in args.valid_runs for row in load_jsonl(path)]
    invalid = flatten(invalid_records, "plausible_unlisted")
    valid = flatten(valid_records, "matched_valid")
    if len(invalid) != 768 or len(valid) != 384:
        raise ValueError(f"unexpected joint grid sizes: invalid={len(invalid)}, valid={len(valid)}")
    rows = invalid + valid
    result = {
        "analysis_kind": "matched valid and plausible unlisted source discrimination",
        "invalid_records": len(invalid),
        "valid_records": len(valid),
        "models": sorted({row["model"] for row in rows}),
        "joint_model_condition": joint_cells(rows),
        "confusion": confusion(rows),
        "invalid_false_eligibility_clustered_by_base_request": clustered_invalid_effect(invalid),
        "invalid_false_eligibility_clustered_by_semantic_case": clustered_invalid_effect_by_semantic_case(invalid),
        "run_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [*args.invalid_runs, *args.valid_runs]
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
