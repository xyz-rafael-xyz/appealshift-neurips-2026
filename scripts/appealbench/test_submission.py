#!/usr/bin/env python3
"""Tests for AI for Peace form validation."""

from __future__ import annotations

import unittest

from validate_submission import AUTHOR_ACTION_REQUIRED, validate


def valid_payload() -> dict[str, object]:
    return {
        "presenter_names": AUTHOR_ACTION_REQUIRED,
        "presenter_emails": AUTHOR_ACTION_REQUIRED,
        "title": "AppealBench",
        "tldr": "A synthetic audit of humanitarian reviews for peace work.",
        "abstract": "We study a synthetic humanitarian review task motivated by peace and accountability.",
        "presentation_format": "Both",
        "work_status": "Novel work",
        "publication_venue": "",
        "in_person_attendance": AUTHOR_ACTION_REQUIRED,
        "other_notes": "",
    }


class SubmissionValidationTests(unittest.TestCase):
    def test_valid_content_preserves_author_gates(self) -> None:
        result = validate(valid_payload())
        self.assertEqual(result["content_status"], "pass")
        self.assertFalse(result["portal_ready"])
        self.assertEqual(len(result["author_only_gates"]), 3)

    def test_limits_and_style_are_enforced(self) -> None:
        payload = valid_payload()
        payload["tldr"] = "x" * 301
        payload["abstract"] = "Synthetic humanitarian peace study: not narrow, but broad; yes—really."
        result = validate(payload)
        self.assertEqual(result["content_status"], "fail")
        joined = "\n".join(result["errors"])
        self.assertIn("above 300", joined)
        self.assertIn("colon", joined)
        self.assertIn("semicolon", joined)
        self.assertIn("em_dash", joined)
        self.assertIn("not-X-but-Y", joined)

    def test_extended_human_language_rules_are_enforced(self) -> None:
        payload = valid_payload()
        payload["tldr"] = "A crucial audit has code, data, and notes."
        payload["abstract"] = "Synthetic humanitarian peace work is not only useful, it is “vibrant”."
        result = validate(payload)
        self.assertEqual(result["content_status"], "fail")
        joined = "\n".join(result["errors"])
        self.assertIn("serial three-part list", joined)
        self.assertIn("negative parallelism", joined)
        self.assertIn("curly_quote", joined)
        self.assertIn("stock promotional wording", joined)


if __name__ == "__main__":
    unittest.main()
