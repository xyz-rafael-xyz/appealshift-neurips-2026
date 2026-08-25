#!/usr/bin/env python3
"""Plot AppealShift disposition accuracy without hiding model heterogeneity."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


CONDITIONS = (
    "independent_review",
    "prior_rationale",
    "evidence_checklist",
    "commit_then_review",
)
CONDITION_LABELS = ("Independent", "Prior rationale", "Checklist", "Commit first")
STATES = ("valid", "invalid", "incomplete", "conflict")
STATE_TITLES = {
    "valid": "Valid appeal evidence",
    "invalid": "Invalid appeal evidence",
    "incomplete": "Incomplete appeal evidence",
    "conflict": "Conflicting appeal evidence",
}
MODEL_ORDER = ("Qwen3-4B", "Phi-4-mini", "Gemma-3-4B", "Mistral-7B")
PDF_TIMESTAMP = datetime(2026, 8, 22, tzinfo=timezone.utc)


def load_analysis(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def figure_cells(
    analysis: Dict[str, object],
) -> Tuple[Dict[Tuple[str, str, str], float], Dict[Tuple[str, str], float]]:
    model_values: Dict[Tuple[str, str, str], float] = {}
    for row in analysis["model_condition_evidence_summaries"]:
        key = (str(row["model"]), str(row["condition"]), str(row["evidence_state"]))
        model_values[key] = float(row["disposition_correct_rate"])
    pooled_values: Dict[Tuple[str, str], float] = {}
    for row in analysis["condition_evidence_summaries"]:
        key = (str(row["condition"]), str(row["evidence_state"]))
        pooled_values[key] = float(row["disposition_correct_rate"])
    return model_values, pooled_values


def validate_grid(
    model_values: Dict[Tuple[str, str, str], float],
    pooled_values: Dict[Tuple[str, str], float],
    models: Sequence[str],
) -> None:
    expected_model = {(m, c, s) for m in models for c in CONDITIONS for s in STATES}
    expected_pooled = {(c, s) for c in CONDITIONS for s in STATES}
    missing_model = expected_model - set(model_values)
    missing_pooled = expected_pooled - set(pooled_values)
    if missing_model or missing_pooled:
        raise ValueError(
            f"incomplete figure grid, missing model cells {len(missing_model)} and pooled cells {len(missing_pooled)}"
        )


def plot(analysis: Dict[str, object], png: Path, pdf: Path) -> None:
    import matplotlib.pyplot as plt

    model_values, pooled_values = figure_cells(analysis)
    observed = sorted({key[0] for key in model_values})
    models: List[str] = [model for model in MODEL_ORDER if model in observed]
    models.extend(model for model in observed if model not in models)
    validate_grid(model_values, pooled_values, models)
    colors = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
    x = list(range(len(CONDITIONS)))
    fig, axes = plt.subplots(1, 4, figsize=(12.0, 3.4), sharey=True)
    for axis, state in zip(axes, STATES):
        for index, model in enumerate(models):
            values = [100 * model_values[(model, condition, state)] for condition in CONDITIONS]
            axis.plot(
                x,
                values,
                marker="o",
                markersize=4.2,
                linewidth=1.25,
                color=colors[index % len(colors)],
                label=model,
                alpha=0.88,
            )
        pooled = [100 * pooled_values[(condition, state)] for condition in CONDITIONS]
        axis.plot(
            x,
            pooled,
            marker="D",
            markersize=5.0,
            linewidth=2.2,
            color="#111111",
            label="Pooled",
            zorder=5,
        )
        axis.set_title(STATE_TITLES[state], fontsize=9.5)
        axis.set_xticks(x, CONDITION_LABELS, rotation=34, ha="right", fontsize=8)
        axis.set_ylim(-2, 102)
        axis.grid(axis="y", linewidth=0.5, alpha=0.35)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Exact disposition accuracy (%)")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, fontsize=8.5)
    fig.subplots_adjust(top=0.78, bottom=0.28, left=0.065, right=0.995, wspace=0.16)
    png.parent.mkdir(parents=True, exist_ok=True)
    pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=220, bbox_inches="tight")
    fig.savefig(
        pdf,
        bbox_inches="tight",
        metadata={"CreationDate": PDF_TIMESTAMP, "ModDate": PDF_TIMESTAMP},
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    args = parser.parse_args()
    plot(load_analysis(args.analysis), args.png, args.pdf)


if __name__ == "__main__":
    main()
