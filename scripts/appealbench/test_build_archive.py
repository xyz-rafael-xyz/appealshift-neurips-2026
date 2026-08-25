#!/usr/bin/env python3
"""Tests for deterministic AppealShift archive creation."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from build_archive import build


class BuildArchiveTests(unittest.TestCase):
    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "b.txt").write_text("b\n", encoding="utf-8")
            (root / "a.md").write_text("a\n", encoding="utf-8")
            first = root / "first.zip"
            second = root / "second.zip"
            one = build(root, first, [Path("data"), Path("a.md")])
            two = build(root, second, [Path("a.md"), Path("data")])
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertEqual([item["path"] for item in one["files"]], ["a.md", "data/b.txt"])

    def test_executable_mode_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "reproduce.sh"
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            script.chmod(0o755)
            output = root / "artifact.zip"
            build(root, output, [Path("reproduce.sh")])
            with zipfile.ZipFile(output) as archive:
                mode = archive.getinfo("reproduce.sh").external_attr >> 16
            self.assertEqual(mode, 0o100755)

    def test_parent_include_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(ValueError):
                build(root, root / "bad.zip", [Path("../outside")])


if __name__ == "__main__":
    unittest.main()
