#!/usr/bin/env python3

import unittest

from analyze import (
    base_case_effects,
    exact_mcnemar,
    paired_cluster_difference,
    leave_one_model_out_confirmatory,
    sign_randomization_test,
    summarize,
)


def analysis_row(case, variant, condition, correct, model="M"):
    row = {
        "case_id": case,
        "variant_id": variant,
        "condition": condition,
        "evidence_state": "valid",
        "model": model,
        "disposition_correct": correct,
        "clause_correct": correct,
        "evidence_correct": correct,
        "fully_grounded": correct,
        "schema_valid": 1,
        "strict_format": 1,
        "failure_to_correct": 1 - correct,
        "false_eligibility": 0,
        "appropriate_information_request": 0,
        "appropriate_human_review": 0,
        "reply_characters": 20,
        "reply_words": 4,
        "unsupported_identifier_count": 0,
        "parser_mode": "strict",
        "changed_disposition": None,
    }
    return row


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            analysis_row("c1", "c1-v", "independent_review", 1),
            analysis_row("c1", "c1-v", "prior_rationale", 0),
            analysis_row("c2", "c2-v", "independent_review", 1),
            analysis_row("c2", "c2-v", "prior_rationale", 1),
        ]

    def test_base_case_effects(self):
        effects = dict(
            base_case_effects(
                self.rows,
                "independent_review",
                "prior_rationale",
                "disposition_correct",
                "valid",
            )
        )
        self.assertEqual(effects, {"c1": -1, "c2": 0})

    def test_cluster_difference_is_deterministic(self):
        first = paired_cluster_difference(
            self.rows,
            "independent_review",
            "prior_rationale",
            "disposition_correct",
            "valid",
            100,
            7,
        )
        second = paired_cluster_difference(
            self.rows,
            "independent_review",
            "prior_rationale",
            "disposition_correct",
            "valid",
            100,
            7,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["difference_b_minus_a"], -0.5)

    def test_sign_randomization_null(self):
        result = sign_randomization_test([0.0, 0.0], 100, 11)
        self.assertEqual(result["p_two_sided"], 1.0)

    def test_mcnemar_counts_direction(self):
        result = exact_mcnemar(
            self.rows,
            "independent_review",
            "prior_rationale",
            "disposition_correct",
            "valid",
        )
        self.assertEqual(result["a1_b0"], 1)
        self.assertEqual(result["a0_b1"], 0)

    def test_summary_rates(self):
        result = summarize(self.rows)
        self.assertEqual(result["n"], 4)
        self.assertEqual(result["disposition_correct_rate"], 0.75)

    def test_leave_one_model_out_exposes_driver(self):
        rows = []
        for case in ("c1", "c2"):
            for model, rationale_correct in (("steady", 0), ("driver", 1)):
                rows.append(
                    analysis_row(
                        case,
                        f"{case}-{model}",
                        "independent_review",
                        0,
                        model=model,
                    )
                )
                rows.append(
                    analysis_row(
                        case,
                        f"{case}-{model}",
                        "prior_rationale",
                        rationale_correct,
                        model=model,
                    )
                )
        result = leave_one_model_out_confirmatory(rows, 100, 7)
        by_drop = {row["dropped_model"]: row for row in result}
        self.assertEqual(by_drop["none"]["effect_rationale_minus_independent"], 0.5)
        self.assertEqual(by_drop["driver"]["effect_rationale_minus_independent"], 0.0)
        self.assertEqual(by_drop["steady"]["effect_rationale_minus_independent"], 1.0)


if __name__ == "__main__":
    unittest.main()
