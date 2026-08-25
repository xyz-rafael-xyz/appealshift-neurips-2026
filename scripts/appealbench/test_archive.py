#!/usr/bin/env python3
"""Tests for AppealShift archive safety validation."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from validate_archive import validate_archive


class ArchiveValidationTests(unittest.TestCase):
    def test_safe_archive_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "safe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("README.md", "synthetic research archive\n")
                archive.writestr("data/cases.jsonl", '{"case":"c1"}\n')
            result = validate_archive(path, ["README.md", "data/cases.jsonl"])
            self.assertEqual(result["status"], "pass")

    def test_unsafe_and_identity_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../escape.txt", "x")
                identity_path = "/Users/" + "rafa" + "el/private"
                archive.writestr("notes.md", identity_path)
                archive.writestr("weights/model.safetensors", b"x")
            result = validate_archive(path, [])
            self.assertEqual(result["status"], "fail")
            self.assertTrue(result["identity_hits"])
            self.assertGreaterEqual(len(result["errors"]), 3)


if __name__ == "__main__":
    unittest.main()
