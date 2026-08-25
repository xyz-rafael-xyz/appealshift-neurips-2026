#!/usr/bin/env python3
"""Tests for the AppealBench run manifest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from make_run_manifest import build_manifest, sha256


class RunManifestTests(unittest.TestCase):
    def test_manifest_binds_files_and_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "data.jsonl"
            models = root / "models.json"
            code = root / "protocol.py"
            run = root / "run.jsonl"
            evidence = root / "validation.json"
            dataset.write_text('{"case_id":"c1"}\n', encoding="utf-8")
            models.write_text('{"models":[]}\n', encoding="utf-8")
            code.write_text("VERSION = 'v1'\n", encoding="utf-8")
            evidence.write_text('{"status":"pass"}\n', encoding="utf-8")
            record = {
                "model": "m",
                "revision": "r",
                "protocol_version": "v1",
                "dataset_sha256": sha256(dataset),
            }
            run.write_text(json.dumps(record) + "\n", encoding="utf-8")

            result = build_manifest(dataset, models, [code], [run], [evidence])

            self.assertEqual(result["total_run_records"], 1)
            self.assertEqual(result["dataset"]["sha256"], sha256(dataset))
            self.assertEqual(result["runs"][0]["models"], ["m"])
            self.assertEqual(result["runs"][0]["revisions"], ["r"])
            self.assertEqual(result["evidence"][0]["sha256"], sha256(evidence))


if __name__ == "__main__":
    unittest.main()
