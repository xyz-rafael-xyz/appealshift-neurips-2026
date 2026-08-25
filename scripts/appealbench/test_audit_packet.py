#!/usr/bin/env python3

import unittest
from collections import Counter

from make_audit_packet import select_records


def fixture(model, condition, state, surface, index):
    return {
        "model": model,
        "condition": condition,
        "evidence_state": state,
        "surface_form": surface,
        "variant_id": f"{model}-{condition}-{state}-{surface}-{index}",
    }


class AuditPacketTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            fixture(model, condition, state, surface, index)
            for model in ("m1", "m2")
            for condition in ("c1", "c2")
            for state in ("valid", "invalid")
            for surface in ("s1", "s2")
            for index in range(5)
        ]

    def test_selection_is_deterministic(self):
        self.assertEqual(
            select_records(self.records, 2, 17), select_records(self.records, 2, 17)
        )

    def test_selection_balances_every_stratum(self):
        selected = select_records(self.records, 2, 17)
        counts = Counter(
            (row["model"], row["condition"], row["evidence_state"], row["surface_form"])
            for row in selected
        )
        self.assertEqual(set(counts.values()), {2})
        self.assertEqual(len(selected), 32)


if __name__ == "__main__":
    unittest.main()
