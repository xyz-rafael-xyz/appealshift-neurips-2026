#!/usr/bin/env python3
"""Independently recompute AppealShift result quantities from frozen runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple


CONDITIONS = (
    "independent_review",
    "prior_rationale",
    "evidence_checklist",
    "commit_then_review",
)
STATES = ("valid", "invalid", "incomplete", "conflict")


def short_model(model: str) -> str:
    return {
        "mlx-community/Qwen3-4B-Instruct-2507-4bit": "Qwen3-4B",
        "mlx-community/Phi-4-mini-instruct-mlx-4Bit": "Phi-4-mini",
        "mlx-community/gemma-3-text-4b-it-4bit": "Gemma-3-4B",
        "mlx-community/Mistral-7B-Instruct-v0.3-4bit": "Mistral-7B",
    }.get(model, model)


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


def quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def flatten(records: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for record in records:
        score = record["score"]
        rows.append(
            {
                "model": short_model(str(record["model"])),
                "case_id": str(record["case_id"]),
                "variant_id": str(record["variant_id"]),
                "condition": str(record["condition"]),
                "evidence_state": str(record["evidence_state"]),
                "surface_form": str(record["surface_form"]),
                "disposition_correct": int(bool(score["disposition_correct"])),
                "fully_grounded": int(bool(score["fully_grounded"])),
                "schema_valid": int(bool(score["schema_valid"])),
                "strict_format": int(bool(score["strict_format"])),
                "false_eligibility": int(bool(score["false_eligibility"])),
                "failure_to_correct": int(bool(score["failure_to_correct"])),
                "appropriate_information_request": int(
                    bool(score["appropriate_information_request"])
                ),
                "appropriate_human_review": int(bool(score["appropriate_human_review"])),
                "parser_mode": str(score["parser_mode"]),
            }
        )
    return rows


def paired_effects(rows: Sequence[Dict[str, object]], model: str | None = None) -> Dict[str, float]:
    cells: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for row in rows:
        if row["evidence_state"] != "valid":
            continue
        if row["condition"] not in {"independent_review", "prior_rationale"}:
            continue
        if model is not None and row["model"] != model:
            continue
        cells[(str(row["case_id"]), str(row["condition"]))].append(
            float(row["disposition_correct"])
        )
    case_ids = sorted(
        case_id
        for case_id, condition in cells
        if condition == "independent_review" and (case_id, "prior_rationale") in cells
    )
    return {
        case_id: mean(cells[(case_id, "prior_rationale")])
        - mean(cells[(case_id, "independent_review")])
        for case_id in case_ids
    }


def confirmatory_recompute(
    rows: Sequence[Dict[str, object]], resamples: int = 20000, seed: int = 20260822
) -> Dict[str, object]:
    effects = paired_effects(rows)
    values = list(effects.values())
    label = "independent_review|prior_rationale|disposition_correct|valid|None"
    rng = random.Random(stable_seed(seed, label))
    boot = [mean(rng.choice(values) for _ in values) for _ in range(resamples)]
    observed = abs(mean(values))
    if observed == 0:
        p_value = 1.0
    else:
        sign_rng = random.Random(stable_seed(seed, "confirmatory_sign_randomization"))
        extreme = 0
        draws = 100000
        for _ in range(draws):
            randomized = mean(value if sign_rng.getrandbits(1) else -value for value in values)
            if abs(randomized) >= observed - 1e-15:
                extreme += 1
        p_value = (extreme + 1) / (draws + 1)
    model_reports = {}
    for model in sorted({str(row["model"]) for row in rows}):
        model_effects = paired_effects(rows, model)
        model_values = list(model_effects.values())
        model_label = (
            f"independent_review|prior_rationale|disposition_correct|valid|{model}"
        )
        model_rng = random.Random(stable_seed(seed, model_label))
        model_boot = [
            mean(model_rng.choice(model_values) for _ in model_values)
            for _ in range(resamples)
        ]
        model_reports[model] = {
            "condition_a": "independent_review",
            "condition_b": "prior_rationale",
            "metric": "disposition_correct",
            "evidence_state": "valid",
            "model": model,
            "n_base_cases": len(model_values),
            "difference_b_minus_a": mean(model_values),
            "ci95": [quantile(model_boot, 0.025), quantile(model_boot, 0.975)],
            "resamples": resamples,
            "seed": seed,
            "base_case_effects": model_effects,
        }
    return {
        "n_base_cases": len(values),
        "difference_b_minus_a": mean(values),
        "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "base_case_effects": effects,
        "p_two_sided": p_value,
        "model_directions": model_reports,
    }


def lomo_recompute(
    rows: Sequence[Dict[str, object]], resamples: int = 20000, seed: int = 20260822
) -> List[Dict[str, object]]:
    """Independently recompute the confirmatory contrast after each model omission."""
    models = sorted({str(row["model"]) for row in rows})
    reports = []
    label = "independent_review|prior_rationale|disposition_correct|valid|None"
    for dropped in [None, *models]:
        selected = rows if dropped is None else [row for row in rows if row["model"] != dropped]
        values = list(paired_effects(selected).values())
        rng = random.Random(stable_seed(seed, label))
        boot = [mean(rng.choice(values) for _ in values) for _ in range(resamples)]
        reports.append(
            {
                "dropped_model": "none" if dropped is None else dropped,
                "models_retained": len(models) if dropped is None else len(models) - 1,
                "effect_rationale_minus_independent": mean(values),
                "ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
                "n_base_cases": len(values),
            }
        )
    return reports


def rates(rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> Dict[Tuple[str, ...], Dict[str, object]]:
    groups: Dict[Tuple[str, ...], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[field]) for field in fields)].append(row)
    metrics = (
        "disposition_correct",
        "fully_grounded",
        "schema_valid",
        "strict_format",
        "false_eligibility",
        "failure_to_correct",
        "appropriate_information_request",
        "appropriate_human_review",
    )
    return {
        key: {
            "n": len(values),
            **{f"{metric}_rate": mean(float(row[metric]) for row in values) for metric in metrics},
            "parser_modes": dict(sorted(Counter(str(row["parser_mode"]) for row in values).items())),
        }
        for key, values in groups.items()
    }


def close(left: object, right: object, tolerance: float = 1e-12) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return all(close(a, b, tolerance) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict) and set(left) == set(right):
        return all(close(left[key], right[key], tolerance) for key in left)
    return left == right


def validate(
    run_paths: Sequence[Path], analysis_path: Path, validation_path: Path
) -> Dict[str, object]:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    run_validation = json.loads(validation_path.read_text(encoding="utf-8"))
    records = [record for path in run_paths for record in load_jsonl(path)]
    rows = flatten(records)
    checks: List[Dict[str, object]] = []

    def check(label: str, observed: object, expected: object) -> None:
        checks.append(
            {"label": label, "pass": close(observed, expected), "observed": observed, "expected": expected}
        )

    check("combined run validation", run_validation.get("status"), "pass")
    check("combined validation errors", run_validation.get("errors"), [])
    check("raw record count", len(records), 3072)
    check("unique model count", len({row["model"] for row in rows}), 4)
    check("analysis record count", analysis.get("records"), len(records))
    for path in run_paths:
        matching = [item for item in analysis["run_files"] if item["path"] == str(path)]
        check(f"analysis hash for {path}", matching[0]["sha256"] if len(matching) == 1 else None, sha256(path))
        check(f"records for {path}", len(load_jsonl(path)), 768)

    cell_counts = Counter((row["model"], row["condition"], row["evidence_state"]) for row in rows)
    check("model condition state cells", len(cell_counts), 64)
    check("records per model condition state", sorted(set(cell_counts.values())), [48])

    independent = confirmatory_recompute(rows)
    reported = analysis["confirmatory"]
    check("confirmatory base cases", reported["n_base_cases"], independent["n_base_cases"])
    check("confirmatory difference", reported["difference_b_minus_a"], independent["difference_b_minus_a"])
    check("confirmatory interval", reported["ci95"], independent["ci95"])
    check("confirmatory case effects", reported["base_case_effects"], independent["base_case_effects"])
    check("confirmatory randomization p", reported["sign_randomization"]["p_two_sided"], independent["p_two_sided"])
    check("confirmatory model directions", reported["model_directions"], independent["model_directions"])

    independent_lomo = lomo_recompute(rows)
    reported_lomo = analysis["leave_one_model_out_confirmatory"]
    check("leave-one-model-out row count", len(reported_lomo), 5)
    for independent_row in independent_lomo:
        dropped = independent_row["dropped_model"]
        matches = [row for row in reported_lomo if row["dropped_model"] == dropped]
        check(f"leave-one-model-out {dropped} unique", len(matches), 1)
        if len(matches) == 1:
            check(
                f"leave-one-model-out {dropped} raw recomputation",
                matches[0],
                independent_row,
            )

    condition_rates = rates(rows, ["condition"])
    for condition in CONDITIONS:
        report = analysis["condition_summaries"][condition]
        recomputed = condition_rates[(condition,)]
        for key, value in recomputed.items():
            check(f"{condition} {key}", report[key], value)

    state_rates = rates(rows, ["condition", "evidence_state"])
    reported_state = {
        (row["condition"], row["evidence_state"]): row
        for row in analysis["condition_evidence_summaries"]
    }
    for key, recomputed in sorted(state_rates.items()):
        report = reported_state[key]
        for metric in (
            "n",
            "disposition_correct_rate",
            "fully_grounded_rate",
            "false_eligibility_rate",
            "failure_to_correct_rate",
            "appropriate_information_request_rate",
            "appropriate_human_review_rate",
            "parser_modes",
        ):
            check(f"{key[0]} {key[1]} {metric}", report[metric], recomputed[metric])

    model_condition_rates = rates(rows, ["model", "condition"])
    reported_model_condition = {
        (row["model"], row["condition"]): row
        for row in analysis["model_condition_summaries"]
    }
    for key, recomputed in sorted(model_condition_rates.items()):
        report = reported_model_condition[key]
        for metric in recomputed:
            check(f"{key[0]} {key[1]} {metric}", report[metric], recomputed[metric])

    model_state_rates = rates(rows, ["model", "condition", "evidence_state"])
    reported_model_state = {
        (row["model"], row["condition"], row["evidence_state"]): row
        for row in analysis["model_condition_evidence_summaries"]
    }
    for key, recomputed in sorted(model_state_rates.items()):
        report = reported_model_state[key]
        for metric in recomputed:
            check(
                f"{key[0]} {key[1]} {key[2]} {metric}",
                report[metric],
                recomputed[metric],
            )

    surface_rates = rates(rows, ["surface_form", "condition"])
    reported_surface = {
        (row["surface_form"], row["condition"]): row
        for row in analysis["surface_summaries"]
    }
    for key, recomputed in sorted(surface_rates.items()):
        report = reported_surface[key]
        for metric in recomputed:
            check(f"{key[0]} {key[1]} {metric}", report[metric], recomputed[metric])

    passed = sum(bool(item["pass"]) for item in checks)
    return {
        "valid": passed == len(checks),
        "checks_passed": passed,
        "checks_total": len(checks),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--run-validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.runs, args.analysis, args.run_validation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
