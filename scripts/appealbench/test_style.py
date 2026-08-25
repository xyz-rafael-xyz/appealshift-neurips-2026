import tempfile
import unittest
from pathlib import Path

from validate_style import validate


class StyleValidationTests(unittest.TestCase):
    def check(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text(text, encoding="utf-8")
            return validate(path)

    def test_clean_text_and_url_pass(self):
        report = self.check("A paired test checks one effect. [Source](https://example.org/a).\n")
        self.assertEqual(report["status"], "pass")

    def test_prohibited_punctuation_and_parallelism_fail(self):
        report = self.check("It is not only fast, but also crucial: look—now; done.\n")
        rules = {item["rule"] for item in report["violations"]}
        self.assertTrue({"em dash", "semicolon", "colon", "negative parallelism"} <= rules)

    def test_serial_triplet_fails(self):
        report = self.check("The package has code, data, and notes.\n")
        self.assertIn("serial three-part list", {item["rule"] for item in report["violations"]})


if __name__ == "__main__":
    unittest.main()
