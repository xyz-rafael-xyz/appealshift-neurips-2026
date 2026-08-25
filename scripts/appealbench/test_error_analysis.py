#!/usr/bin/env python3

import unittest

from error_analysis import confusion_rows, paired_failures, surface_disagreements


def fixture(condition, surface, disposition, correct):
    return {
        "model": "m",
        "condition": condition,
        "case_id": "c",
        "variant_id": f"c--{surface}",
        "evidence_state": "valid",
        "surface_form": surface,
        "target_disposition": "ELIGIBLE",
        "score": {"disposition": disposition, "disposition_correct": correct},
    }


class ErrorAnalysisTests(unittest.TestCase):
    def test_confusion_counts(self):
        rows = [fixture("independent_review", "policy_first", "ELIGIBLE", True)]
        self.assertEqual(confusion_rows(rows)[0]["count"], 1)

    def test_paired_failure_direction(self):
        rows = [
            fixture("independent_review", "policy_first", "INELIGIBLE", False),
            fixture("evidence_checklist", "policy_first", "ELIGIBLE", True),
        ]
        result = paired_failures(rows)
        self.assertEqual(result[0]["change_kind"], "corrective")

    def test_surface_disagreement(self):
        rows = [
            fixture("independent_review", "policy_first", "ELIGIBLE", True),
            fixture("independent_review", "record_first", "INELIGIBLE", False),
        ]
        self.assertEqual(len(surface_disagreements(rows)), 1)


if __name__ == "__main__":
    unittest.main()
