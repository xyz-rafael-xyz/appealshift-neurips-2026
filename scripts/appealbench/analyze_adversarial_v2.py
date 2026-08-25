#!/usr/bin/env python3
"""Analyze the prospectively frozen plausible-source v2 experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path


SEED = 20260824
RESAMPLES = 20000


def load_jsonl(file_name: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in file_name.read_text(encoding="utf-8").splitlines() if line.strip()]


def mean(values) -> float:
    values = list(values)
    return statistics.fmean(values) if values else math.nan


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def short_model(model: str) -> str:
    return {
        "mlx-community/Qwen3-4B-Instruct-2507-4bit": "Qwen3-4B",
        "mlx-community/Mistral-7B-Instruct-v0.3-4bit": "Mistral-7B",
        "mlx-community/Phi-4-mini-instruct-mlx-4Bit": "Phi-4-mini",
        "mlx-community/gemma-3-text-4b-it-4bit": "Gemma-3-4B",
    }.get(model, model)


def flatten(record: dict[str, object], cases: dict[str, dict[str, object]]) -> dict[str, object]:
    score = record["score"]
    source = cases[str(record["variant_id"])]
    return {
        "model": short_model(str(record["model"])),
        "model_id": record["model"],
        "case_id": record["case_id"],
        "variant_id": record["variant_id"],
        "source_variant": source["source_variant"],
        "surface_form": record["surface_form"],
        "condition": record["condition"],
        "disposition_correct": int(bool(score["disposition_correct"])),
        "false_eligibility": int(bool(score["false_eligibility"])),
        "fully_grounded": int(bool(score["fully_grounded"])),
        "appropriate_information_request": int(bool(score["appropriate_information_request"])),
    }


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "n": len(rows),
        "disposition_accuracy": mean(int(row["disposition_correct"]) for row in rows),
        "false_eligibility_rate": mean(int(row["false_eligibility"]) for row in rows),
        "fully_grounded_rate": mean(int(row["fully_grounded"]) for row in rows),
        "appropriate_information_request_rate": mean(int(row["appropriate_information_request"]) for row in rows),
    }


def paired_effect(rows: list[dict[str, object]], metric: str) -> dict[str, object]:
    grouped: dict[tuple[str, str, str], dict[str, int]] = defaultdict(dict)
    for row in rows:
        key = (str(row["model"]), str(row["case_id"]), str(row["surface_form"]))
        grouped[key][str(row["condition"])] = int(row[metric])
    effects = [
        pair["prior_rationale"] - pair["independent_review"]
        for pair in grouped.values()
        if {"independent_review", "prior_rationale"} <= pair.keys()
    ]
    rng = random.Random(SEED + int(hashlib.sha256(metric.encode()).hexdigest()[:8], 16))
    boot = [mean(rng.choice(effects) for _ in effects) for _ in range(RESAMPLES)]
    return {
        "metric": metric,
        "n_paired_model_case_surfaces": len(effects),
        "prior_minus_independent": mean(effects),
        "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "bootstrap_seed": SEED,
        "bootstrap_resamples": RESAMPLES,
        "clustering_note": "The descriptive bootstrap resamples paired model-case-surface effects; fixed model artifacts are not a population sample.",
    }


def grouped(rows: list[dict[str, object]], fields: tuple[str, ...]) -> list[dict[str, object]]:
    cells: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        cells[tuple(str(row[field]) for field in fields)].append(row)
    output = []
    for key, values in sorted(cells.items()):
        output.append({**dict(zip(fields, key)), **summarize(values)})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/appealbench/adversarial_v2.jsonl"))
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, default=Path("experiments/appealbench/adversarial_v2_analysis.json"))
    args = parser.parse_args()
    cases = {str(row["variant_id"]): row for row in load_jsonl(args.dataset)}
    records = [row for file_name in args.runs for row in load_jsonl(file_name)]
    rows = [flatten(record, cases) for record in records]
    result = {
        "analysis_kind": "prospectively frozen plausible-source v2",
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "records": len(rows),
        "semantic_cases": len({str(row["case_id"]) for row in rows}),
        "models": sorted({str(row["model"]) for row in rows}),
        "overall": summarize(rows),
        "by_condition": grouped(rows, ("condition",)),
        "by_model_condition": grouped(rows, ("model", "condition")),
        "by_source_condition": grouped(rows, ("source_variant", "condition")),
        "by_surface_condition": grouped(rows, ("surface_form", "condition")),
        "paired_condition_effects": {
            metric: paired_effect(rows, metric)
            for metric in ("disposition_correct", "false_eligibility", "fully_grounded")
        },
        "run_sha256": {str(file_name): hashlib.sha256(file_name.read_bytes()).hexdigest() for file_name in args.runs},
    }
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
