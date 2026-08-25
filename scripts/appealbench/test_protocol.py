#!/usr/bin/env python3

import copy
import json
import unittest

from audit_scorer import audit_score
from generate_dataset import evaluation_rows
from protocol import (
    CONDITIONS,
    final_commit_messages,
    initial_messages,
    prompt_hash,
    score_output,
)


def row_for(state):
    return next(
        row
        for row in evaluation_rows()
        if row["evidence_state"] == state and row["surface_form"] == "policy_first"
    )


def correct_output(row):
    return json.dumps(
        {
            "disposition": row["target_disposition"],
            "policy_clause": row["target_clause"],
            "evidence_ids": row["target_evidence_ids"],
            "reply": "The current evidence supports this disposition.",
        }
    )


class PromptTests(unittest.TestCase):
    def test_all_conditions_build(self):
        row = row_for("valid")
        for condition in CONDITIONS:
            messages = initial_messages(row, condition)
            self.assertEqual([message["role"] for message in messages], ["system", "user"])

    def test_prior_rationale_is_hidden_in_independent_prompt(self):
        row = row_for("valid")
        independent = json.dumps(initial_messages(row, "independent_review"))
        prior = json.dumps(initial_messages(row, "prior_rationale"))
        rationale = row["prior_denial"]["rationale"]
        self.assertNotIn(rationale, independent)
        self.assertIn(rationale, prior)

    def test_checklist_instruction_is_condition_specific(self):
        row = row_for("valid")
        checklist = initial_messages(row, "evidence_checklist")[0]["content"]
        ordinary = initial_messages(row, "prior_rationale")[0]["content"]
        self.assertIn("compare each appeal evidence item", checklist)
        self.assertNotIn("compare each appeal evidence item", ordinary)

    def test_decision_order_is_present_in_every_case_prompt(self):
        row = row_for("conflict")
        for condition in CONDITIONS:
            text = initial_messages(row, condition)[1]["content"]
            self.assertIn("Apply C4 first", text)
            self.assertIn("Apply C1 only", text)

    def test_commit_final_contains_preliminary_as_data(self):
        row = row_for("valid")
        messages = final_commit_messages(row, '{"disposition":"INELIGIBLE"}')
        self.assertIn("<preliminary>", messages[1]["content"])
        self.assertIn(row["prior_denial"]["rationale"], messages[1]["content"])

    def test_prompt_hash_is_stable(self):
        row = row_for("invalid")
        messages = initial_messages(row, "prior_rationale")
        self.assertEqual(prompt_hash(messages), prompt_hash(copy.deepcopy(messages)))


class ScoringTests(unittest.TestCase):
    def test_correct_outputs_for_all_targets(self):
        for state in ("valid", "invalid", "incomplete", "conflict"):
            row = row_for(state)
            score = score_output(row, correct_output(row))
            self.assertTrue(score["strict_format"])
            self.assertTrue(score["fully_grounded"])

    def test_recovered_json_is_not_strict(self):
        row = row_for("valid")
        score = score_output(row, f"```json\n{correct_output(row)}\n```")
        self.assertEqual(score["parser_mode"], "recovered")
        self.assertFalse(score["strict_format"])
        self.assertTrue(score["fully_grounded"])

    def test_extra_key_breaks_schema(self):
        row = row_for("valid")
        value = json.loads(correct_output(row))
        value["analysis"] = "extra"
        score = score_output(row, json.dumps(value))
        self.assertFalse(score["schema_valid"])
        self.assertFalse(score["fully_grounded"])

    def test_unknown_identifier_is_reported(self):
        row = row_for("valid")
        value = json.loads(correct_output(row))
        value["evidence_ids"] = ["E9"]
        score = score_output(row, json.dumps(value))
        self.assertEqual(score["unsupported_identifiers"], ["E9"])
        self.assertFalse(score["schema_valid"])

    def test_duplicate_evidence_breaks_schema(self):
        row = row_for("conflict")
        value = json.loads(correct_output(row))
        value["evidence_ids"] = ["E1", "E1"]
        self.assertFalse(score_output(row, json.dumps(value))["schema_valid"])

    def test_failure_and_false_eligibility_flags(self):
        valid = row_for("valid")
        invalid = row_for("invalid")
        bad_valid = json.loads(correct_output(valid))
        bad_valid["disposition"] = "INELIGIBLE"
        bad_invalid = json.loads(correct_output(invalid))
        bad_invalid["disposition"] = "ELIGIBLE"
        self.assertTrue(score_output(valid, json.dumps(bad_valid))["failure_to_correct"])
        self.assertTrue(score_output(invalid, json.dumps(bad_invalid))["false_eligibility"])

    def test_independent_audit_scorer_agrees(self):
        for state in ("valid", "invalid", "incomplete", "conflict"):
            row = row_for(state)
            raw = correct_output(row)
            primary = score_output(row, raw)
            audit = audit_score(row, raw)
            for key in audit:
                self.assertEqual(primary[key], audit[key], key)

    def test_identifier_rename_preserves_disposition_and_updates_grounding(self):
        row = copy.deepcopy(row_for("valid"))
        row["appeal_evidence"][0]["id"] = "Z7"
        row["target_evidence_ids"] = ["Z7"]
        value = json.loads(correct_output(row))
        score = score_output(row, json.dumps(value))
        self.assertTrue(score["disposition_correct"])
        self.assertTrue(score["evidence_correct"])


if __name__ == "__main__":
    unittest.main()
