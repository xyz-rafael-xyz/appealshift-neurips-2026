#!/usr/bin/env python3
"""Tests for completed human audit scoring."""

from __future__ import annotations

import unittest

from score_human_audit import cohen_kappa, compare


class HumanAuditTests(unittest.TestCase):
    def test_exact_audit_scores_perfectly(self) -> None:
        packet = [
            {
                "audit_id": "a1",
                "reviewer_fields": {
                    "disposition": "ELIGIBLE",
                    "policy_clause": "C1",
                    "evidence_ids": ["E1"],
                    "schema_valid": True,
                    "notes": None,
                },
            }
        ]
        key = [
            {
                "audit_id": "a1",
                "independent_audit_score": {
                    "disposition": "ELIGIBLE",
                    "policy_clause": "C1",
                    "evidence_ids": ["E1"],
                    "schema_valid": True,
                },
            }
        ]
        report = compare(packet, key)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["agreement"]["disposition"], 1.0)
        self.assertEqual(report["disagreements"], [])

    def test_incomplete_labels_are_rejected(self) -> None:
        packet = [{"audit_id": "a1", "reviewer_fields": {"disposition": None}}]
        key = [{"audit_id": "a1", "independent_audit_score": {}}]
        with self.assertRaises(ValueError):
            compare(packet, key)

    def test_unparseable_labels_map_to_missing_machine_fields(self) -> None:
        packet = [
            {
                "audit_id": "a1",
                "reviewer_fields": {
                    "disposition": "UNPARSEABLE",
                    "policy_clause": "",
                    "evidence_ids": [],
                    "schema_valid": False,
                },
            }
        ]
        key = [
            {
                "audit_id": "a1",
                "independent_audit_score": {
                    "disposition": None,
                    "policy_clause": None,
                    "evidence_ids": [],
                    "schema_valid": False,
                },
            }
        ]
        report = compare(packet, key)
        self.assertEqual(report["disagreements"], [])

    def test_kappa_handles_balanced_agreement(self) -> None:
        self.assertEqual(cohen_kappa(["a", "b"], ["a", "b"]), 1.0)


if __name__ == "__main__":
    unittest.main()
