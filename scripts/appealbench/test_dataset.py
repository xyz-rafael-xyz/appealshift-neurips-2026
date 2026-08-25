#!/usr/bin/env python3

import unittest
from collections import Counter, defaultdict

from generate_dataset import EVIDENCE_STATES, development_rows, evaluation_rows


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.evaluation = evaluation_rows()
        self.development = development_rows()

    def test_evaluation_size(self):
        self.assertEqual(len(self.evaluation), 192)
        self.assertEqual(len({row["case_id"] for row in self.evaluation}), 96)

    def test_development_size(self):
        self.assertEqual(len(self.development), 16)
        self.assertEqual(len({row["case_id"] for row in self.development}), 16)

    def test_target_balance(self):
        counts = Counter(row["target_disposition"] for row in self.evaluation)
        self.assertEqual(set(counts.values()), {48})

    def test_service_state_balance(self):
        first_variants = {
            row["case_id"]: row for row in self.evaluation if row["surface_form"] == "policy_first"
        }
        counts = Counter(
            (row["service_family"], row["evidence_state"])
            for row in first_variants.values()
        )
        self.assertEqual(len(counts), 8 * len(EVIDENCE_STATES))
        self.assertEqual(set(counts.values()), {3})

    def test_surface_pairs_are_semantically_identical(self):
        pairs = defaultdict(list)
        for row in self.evaluation:
            pairs[row["case_id"]].append(row)
        for variants in pairs.values():
            self.assertEqual(len(variants), 2)
            self.assertEqual(len({row["semantic_sha256"] for row in variants}), 1)
            self.assertEqual({row["surface_form"] for row in variants}, {"policy_first", "record_first"})

    def test_split_identifiers_do_not_overlap(self):
        evaluation_ids = {row["request_id"] for row in self.evaluation}
        development_ids = {row["request_id"] for row in self.development}
        self.assertFalse(evaluation_ids & development_ids)

    def test_safety_flags(self):
        for row in self.evaluation + self.development:
            self.assertIs(row["synthetic"], True)
            self.assertIs(row["operational_use_allowed"], False)

    def test_conflict_has_two_decisive_records(self):
        conflicts = [row for row in self.evaluation if row["evidence_state"] == "conflict"]
        self.assertTrue(conflicts)
        for row in conflicts:
            self.assertEqual(row["target_evidence_ids"], ["E1", "E2"])
            self.assertEqual(row["target_disposition"], "HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
