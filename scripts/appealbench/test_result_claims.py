#!/usr/bin/env python3
"""Tests for independent AppealShift result recomputation."""

from __future__ import annotations

import unittest

from validate_result_claims import confirmatory_recompute, flatten, rates


class ResultClaimTests(unittest.TestCase):
    def test_paired_effect_uses_case_clusters(self) -> None:
        records = []
        for model in ("m1", "m2"):
            for case_id, a, b in (("c1", 1, 0), ("c2", 0, 1)):
                for surface in ("p", "r"):
                    for condition, correct in (("independent_review", a), ("prior_rationale", b)):
                        records.append(
                            {
                                "model": model,
                                "case_id": case_id,
                                "variant_id": f"{case_id}-{surface}",
                                "surface_form": surface,
                                "condition": condition,
                                "evidence_state": "valid",
                                "score": {
                                    "disposition_correct": bool(correct),
                                    "fully_grounded": False,
                                    "schema_valid": True,
                                    "strict_format": True,
                                    "false_eligibility": False,
                                    "failure_to_correct": not bool(correct),
                                    "appropriate_information_request": False,
                                    "appropriate_human_review": False,
                                    "parser_mode": "strict",
                                },
                            }
                        )
        result = confirmatory_recompute(flatten(records), resamples=100, seed=4)
        self.assertEqual(result["n_base_cases"], 2)
        self.assertEqual(result["difference_b_minus_a"], 0.0)
        self.assertEqual(result["p_two_sided"], 1.0)
        self.assertEqual(result["base_case_effects"], {"c1": -1.0, "c2": 1.0})

    def test_rates_report_parser_counts(self) -> None:
        rows = [
            {
                "condition": "a",
                "disposition_correct": value,
                "fully_grounded": value,
                "schema_valid": 1,
                "strict_format": value,
                "false_eligibility": 0,
                "failure_to_correct": 0,
                "appropriate_information_request": 0,
                "appropriate_human_review": 0,
                "parser_mode": mode,
            }
            for value, mode in ((1, "strict"), (0, "recovered"))
        ]
        result = rates(rows, ["condition"])[("a",)]
        self.assertEqual(result["disposition_correct_rate"], 0.5)
        self.assertEqual(result["parser_modes"], {"recovered": 1, "strict": 1})


if __name__ == "__main__":
    unittest.main()
