#!/usr/bin/env python3

import unittest

from evaluate_development_gate import DISPOSITIONS, STATES, evaluate


def record(state, disposition, correct, parser_mode="strict"):
    return {
        "evidence_state": state,
        "score": {
            "disposition": disposition,
            "disposition_correct": correct,
            "parser_mode": parser_mode,
        },
    }


class DevelopmentGateTests(unittest.TestCase):
    def test_gate_passes_complete_variable_fixture(self):
        records = []
        for index in range(256):
            state = STATES[index % 4]
            disposition = DISPOSITIONS[index % 4]
            records.append(record(state, disposition, True))
        validation = {
            "status": "pass",
            "run_files": [{"primary_audit_disagreements": 0} for _ in range(4)],
        }
        self.assertEqual(evaluate(records, validation)["decision"], "proceed_to_evaluation")

    def test_gate_stops_on_collapsed_disposition(self):
        records = [record(STATES[index % 4], "ELIGIBLE", True) for index in range(256)]
        validation = {"status": "pass", "run_files": []}
        self.assertEqual(evaluate(records, validation)["decision"], "stop_and_revise")


if __name__ == "__main__":
    unittest.main()
