#!/usr/bin/env python3
"""Analyze frozen AppealBench runs with paired case-cluster uncertainty."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple


CONDITION_ORDER = (
    "independent_review",
    "prior_rationale",
    "evidence_checklist",
    "commit_then_review",
)
BINARY_METRICS = (
    "disposition_correct",
    "clause_correct",
    "evidence_correct",
    "fully_grounded",
    "schema_valid",
    "strict_format",
    "failure_to_correct",
    "false_eligibility",
    "appropriate_information_request",
    "appropriate_human_review",
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


def short_model(model: str) -> str:
    names = {
        "mlx-community/Qwen3-4B-Instruct-2507-4bit": "Qwen3-4B",
        "mlx-community/Phi-4-mini-instruct-mlx-4Bit": "Phi-4-mini",
        "mlx-community/gemma-3-text-4b-it-4bit": "Gemma-3-4B",
        "mlx-community/Mistral-7B-Instruct-v0.3-4bit": "Mistral-7B",
    }
    return names.get(model, model)


def flatten(record: Dict[str, object]) -> Dict[str, object]:
    score = record["score"]
    row = {
        "model": short_model(str(record["model"])),
        "model_id": record["model"],
        "revision": record["revision"],
        "case_id": record["case_id"],
        "variant_id": record["variant_id"],
        "service_family": record["service_family"],
        "surface_form": record["surface_form"],
        "evidence_state": record["evidence_state"],
        "target_disposition": record["target_disposition"],
        "condition": record["condition"],
        "parser_mode": score["parser_mode"],
        "predicted_disposition": score["disposition"],
        "reply_characters": score["reply_characters"],
        "reply_words": score["reply_words"],
        "unsupported_identifier_count": len(score["unsupported_identifiers"]),
    }
    for metric in BINARY_METRICS:
        row[metric] = int(bool(score[metric]))
    update = record.get("update")
    for field in ("changed_disposition", "corrective_update", "harmful_update"):
        row[field] = None if update is None else int(bool(update[field]))
    preliminary = record.get("preliminary_score")
    row["preliminary_correct"] = (
        None if preliminary is None else int(bool(preliminary["disposition_correct"]))
    )
    return row


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> List[float] | None:
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [center - radius, center + radius]


def summarize(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    report: Dict[str, object] = {"n": len(rows)}
    for metric in BINARY_METRICS:
        values = [int(row[metric]) for row in rows]
        successes = sum(values)
        report[f"{metric}_rate"] = successes / len(values) if values else None
        report[f"{metric}_ci95"] = wilson_interval(successes, len(values))
    report["mean_reply_characters"] = (
        mean(float(row["reply_characters"]) for row in rows) if rows else None
    )
    report["mean_reply_words"] = mean(float(row["reply_words"]) for row in rows) if rows else None
    report["unsupported_identifier_count"] = sum(
        int(row["unsupported_identifier_count"]) for row in rows
    )
    report["parser_modes"] = dict(sorted(Counter(str(row["parser_mode"]) for row in rows).items()))
    update_rows = [row for row in rows if row["changed_disposition"] is not None]
    if update_rows:
        for metric in ("changed_disposition", "corrective_update", "harmful_update"):
            report[f"{metric}_rate"] = mean(float(row[metric]) for row in update_rows)
        report["update_n"] = len(update_rows)
    return report


def quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def stable_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}|{label}".encode()).digest()
    return seed + int.from_bytes(digest[:8], "big")


def base_case_effects(
    rows: Sequence[Dict[str, object]],
    condition_a: str,
    condition_b: str,
    metric: str,
    evidence_state: str | None = None,
    model: str | None = None,
) -> List[Tuple[str, float]]:
    cells: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for row in rows:
        if row["condition"] not in {condition_a, condition_b}:
            continue
        if evidence_state is not None and row["evidence_state"] != evidence_state:
            continue
        if model is not None and row["model"] != model:
            continue
        cells[(str(row["case_id"]), str(row["condition"]))].append(float(row[metric]))
    case_ids = sorted(
        case_id
        for case_id, condition in cells
        if condition == condition_a and (case_id, condition_b) in cells
    )
    return [
        (
            case_id,
            mean(cells[(case_id, condition_b)]) - mean(cells[(case_id, condition_a)]),
        )
        for case_id in case_ids
    ]


def paired_cluster_difference(
    rows: Sequence[Dict[str, object]],
    condition_a: str,
    condition_b: str,
    metric: str,
    evidence_state: str | None,
    resamples: int,
    seed: int,
    model: str | None = None,
) -> Dict[str, object]:
    effects = base_case_effects(
        rows, condition_a, condition_b, metric, evidence_state=evidence_state, model=model
    )
    values = [effect for _, effect in effects]
    if not values:
        return {"n_base_cases": 0, "difference_b_minus_a": None, "ci95": None}
    label = f"{condition_a}|{condition_b}|{metric}|{evidence_state}|{model}"
    rng = random.Random(stable_seed(seed, label))
    boot = [mean(rng.choice(values) for _ in values) for _ in range(resamples)]
    return {
        "condition_a": condition_a,
        "condition_b": condition_b,
        "metric": metric,
        "evidence_state": evidence_state,
        "model": model,
        "n_base_cases": len(values),
        "difference_b_minus_a": mean(values),
        "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "resamples": resamples,
        "seed": seed,
        "base_case_effects": {case_id: value for case_id, value in effects},
    }


def sign_randomization_test(
    effects: Sequence[float], draws: int, seed: int
) -> Dict[str, object]:
    if not effects:
        return {"n_base_cases": 0, "p_two_sided": None}
    observed = abs(mean(effects))
    if observed == 0:
        return {
            "n_base_cases": len(effects),
            "observed_absolute_mean": 0.0,
            "p_two_sided": 1.0,
            "draws": draws,
            "seed": seed,
        }
    rng = random.Random(stable_seed(seed, "confirmatory_sign_randomization"))
    extreme = 0
    for _ in range(draws):
        randomized = mean(value if rng.getrandbits(1) else -value for value in effects)
        if abs(randomized) >= observed - 1e-15:
            extreme += 1
    return {
        "n_base_cases": len(effects),
        "observed_absolute_mean": observed,
        "p_two_sided": (extreme + 1) / (draws + 1),
        "draws": draws,
        "seed": seed,
    }


def exact_mcnemar(
    rows: Sequence[Dict[str, object]],
    condition_a: str,
    condition_b: str,
    metric: str,
    evidence_state: str | None = None,
) -> Dict[str, object]:
    cells: Dict[Tuple[str, str, str], int] = {}
    for row in rows:
        if row["condition"] not in {condition_a, condition_b}:
            continue
        if evidence_state is not None and row["evidence_state"] != evidence_state:
            continue
        cells[(str(row["model"]), str(row["variant_id"]), str(row["condition"]))] = int(
            row[metric]
        )
    pairs = []
    for model, variant, condition in sorted(cells):
        if condition != condition_a:
            continue
        other = (model, variant, condition_b)
        if other in cells:
            pairs.append((cells[(model, variant, condition_a)], cells[other]))
    a1_b0 = sum(a == 1 and b == 0 for a, b in pairs)
    a0_b1 = sum(a == 0 and b == 1 for a, b in pairs)
    discordant = a1_b0 + a0_b1
    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(math.comb(discordant, k) for k in range(min(a1_b0, a0_b1) + 1)) / (
            2**discordant
        )
        p_value = min(1.0, 2 * tail)
    return {
        "n_pairs": len(pairs),
        "a1_b0": a1_b0,
        "a0_b1": a0_b1,
        "exact_two_sided_p": p_value,
        "note": "descriptive because semantic cases contribute repeated model and surface-form pairs",
    }


def grouped_summaries(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> List[Dict[str, object]]:
    groups: Dict[Tuple[str, ...], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[field]) for field in fields)].append(row)
    output = []
    for key, values in sorted(groups.items()):
        record = {field: value for field, value in zip(fields, key)}
        record.update(summarize(values))
        output.append(record)
    return output


def leave_one_model_out_confirmatory(
    rows: Sequence[Dict[str, object]], resamples: int, seed: int
) -> List[Dict[str, object]]:
    """Recompute the valid-appeal contrast after omitting each fixed model artifact."""
    models = sorted({str(row["model"]) for row in rows})
    reports: List[Dict[str, object]] = []
    for dropped in [None, *models]:
        selected = rows if dropped is None else [row for row in rows if row["model"] != dropped]
        result = paired_cluster_difference(
            selected,
            "independent_review",
            "prior_rationale",
            "disposition_correct",
            "valid",
            resamples,
            seed,
        )
        reports.append(
            {
                "dropped_model": "none" if dropped is None else dropped,
                "models_retained": len(models) if dropped is None else len(models) - 1,
                "effect_rationale_minus_independent": result["difference_b_minus_a"],
                "ci95": result["ci95"],
                "n_base_cases": result["n_base_cases"],
            }
        )
    return reports


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("experiments/appealbench/full_analysis")
    )
    parser.add_argument("--bootstrap-resamples", type=int, default=20000)
    parser.add_argument("--randomization-draws", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260822)
    args = parser.parse_args()
    records = [record for path in args.runs for record in load_jsonl(path)]
    rows = [flatten(record) for record in records]
    confirmatory = paired_cluster_difference(
        rows,
        "independent_review",
        "prior_rationale",
        "disposition_correct",
        "valid",
        args.bootstrap_resamples,
        args.seed,
    )
    effect_values = list(confirmatory["base_case_effects"].values())
    confirmatory["sign_randomization"] = sign_randomization_test(
        effect_values, args.randomization_draws, args.seed
    )
    confirmatory["descriptive_mcnemar"] = exact_mcnemar(
        rows,
        "independent_review",
        "prior_rationale",
        "disposition_correct",
        "valid",
    )
    models = sorted({str(row["model"]) for row in rows})
    confirmatory["model_directions"] = {
        model: paired_cluster_difference(
            rows,
            "independent_review",
            "prior_rationale",
            "disposition_correct",
            "valid",
            args.bootstrap_resamples,
            args.seed,
            model=model,
        )
        for model in models
    }

    exploratory_specs = (
        ("prior_rationale", "evidence_checklist", "disposition_correct", None),
        ("prior_rationale", "commit_then_review", "disposition_correct", None),
        ("prior_rationale", "evidence_checklist", "disposition_correct", "valid"),
        ("prior_rationale", "commit_then_review", "disposition_correct", "valid"),
        ("prior_rationale", "evidence_checklist", "false_eligibility", "invalid"),
        ("prior_rationale", "commit_then_review", "false_eligibility", "invalid"),
    )
    exploratory = [
        paired_cluster_difference(
            rows, a, b, metric, state, args.bootstrap_resamples, args.seed
        )
        for a, b, metric, state in exploratory_specs
    ]
    condition_slices = grouped_summaries(rows, ("condition",))
    report = {
        "analysis_kind": "AppealBench frozen analysis",
        "records": len(rows),
        "models": models,
        "conditions": list(CONDITION_ORDER),
        "run_files": [
            {"path": str(path), "sha256": sha256(path), "records": len(load_jsonl(path))}
            for path in args.runs
        ],
        "confirmatory": confirmatory,
        "leave_one_model_out_confirmatory": leave_one_model_out_confirmatory(
            rows, args.bootstrap_resamples, args.seed
        ),
        "exploratory_contrasts": exploratory,
        "condition_summaries": {row["condition"]: row for row in condition_slices},
        "condition_evidence_summaries": grouped_summaries(
            rows, ("condition", "evidence_state")
        ),
        "model_condition_summaries": grouped_summaries(rows, ("model", "condition")),
        "model_condition_evidence_summaries": grouped_summaries(
            rows, ("model", "condition", "evidence_state")
        ),
        "surface_summaries": grouped_summaries(rows, ("surface_form", "condition")),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "records.csv", rows)
    write_csv(args.output_dir / "condition_slices.csv", condition_slices)
    write_csv(
        args.output_dir / "lomo_confirmatory.csv",
        report["leave_one_model_out_confirmatory"],
    )
    (args.output_dir / "analysis.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
