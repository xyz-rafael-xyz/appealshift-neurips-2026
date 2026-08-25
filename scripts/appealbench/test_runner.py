#!/usr/bin/env python3

import unittest

from run_mlx import fold_system_into_first_user, slugify


class RunnerTests(unittest.TestCase):
    def test_fold_preserves_content(self):
        messages = [
            {"role": "system", "content": "SYSTEM CONTENT"},
            {"role": "user", "content": "USER CONTENT"},
        ]
        folded = fold_system_into_first_user(messages)
        self.assertEqual(len(folded), 1)
        self.assertIn("SYSTEM CONTENT", folded[0]["content"])
        self.assertIn("USER CONTENT", folded[0]["content"])

    def test_fold_rejects_wrong_shape(self):
        with self.assertRaises(ValueError):
            fold_system_into_first_user([{"role": "user", "content": "only"}])

    def test_slugify(self):
        self.assertEqual(slugify("Vendor/Model 4B"), "vendor-model-4b")


if __name__ == "__main__":
    unittest.main()
