#!/usr/bin/env python3
"""Tests for the AppealShift result figure."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from plot_results import CONDITIONS, STATES, figure_cells, plot, validate_grid


class PlotResultTests(unittest.TestCase):
    def test_complete_grid_is_accepted(self) -> None:
        models = ["m1", "m2"]
        analysis = {
            "model_condition_evidence_summaries": [
                {
                    "model": model,
                    "condition": condition,
                    "evidence_state": state,
                    "disposition_correct_rate": 0.5,
                }
                for model in models
                for condition in CONDITIONS
                for state in STATES
            ],
            "condition_evidence_summaries": [
                {
                    "condition": condition,
                    "evidence_state": state,
                    "disposition_correct_rate": 0.5,
                }
                for condition in CONDITIONS
                for state in STATES
            ],
        }
        model_values, pooled_values = figure_cells(analysis)
        validate_grid(model_values, pooled_values, models)
        self.assertEqual(len(model_values), 32)
        self.assertEqual(len(pooled_values), 16)

    def test_missing_cell_is_rejected(self) -> None:
        model_values = {
            ("m1", condition, state): 0.5
            for condition in CONDITIONS
            for state in STATES
        }
        model_values.pop(("m1", CONDITIONS[0], STATES[0]))
        pooled_values = {
            (condition, state): 0.5 for condition in CONDITIONS for state in STATES
        }
        with self.assertRaises(ValueError):
            validate_grid(model_values, pooled_values, ["m1"])

    def test_pdf_is_byte_deterministic(self) -> None:
        analysis = {
            "model_condition_evidence_summaries": [
                {
                    "model": "m1",
                    "condition": condition,
                    "evidence_state": state,
                    "disposition_correct_rate": 0.5,
                }
                for condition in CONDITIONS
                for state in STATES
            ],
            "condition_evidence_summaries": [
                {
                    "condition": condition,
                    "evidence_state": state,
                    "disposition_correct_rate": 0.5,
                }
                for condition in CONDITIONS
                for state in STATES
            ],
        }
        with TemporaryDirectory() as directory:
            root = Path(directory)
            plot(analysis, root / "first.png", root / "first.pdf")
            plot(analysis, root / "second.png", root / "second.pdf")
            self.assertEqual(
                (root / "first.pdf").read_bytes(),
                (root / "second.pdf").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
