#!/usr/bin/env python3
"""Check AppealShift prose against the author's stated style constraints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


PATTERNS = {
    "em dash": re.compile("—"),
    "semicolon": re.compile(";"),
    "colon": re.compile(":"),
    "curly quotation mark": re.compile("[“”]"),
    "not-X-but-Y construction": re.compile(
        r"\bnot\s+[^.!?\n]{1,80}\bbut\b", flags=re.IGNORECASE
    ),
    "negative parallelism": re.compile(
        r"\b(?:not only|not just|neither\b[^.!?\n]{1,80}\bnor)\b", flags=re.IGNORECASE
    ),
    "serial three-part list": re.compile(
        r",\s+[^,.\n]{1,80},\s+(?:and|or)\s+[^,.\n]{1,80}[.!?]", flags=re.IGNORECASE
    ),
    "stock AI vocabulary": re.compile(
        r"\b(?:additionally|crucial|delve|pivotal|showcas(?:e|es|ed|ing)|"
        r"testament|tapestry|underscor(?:e|es|ed|ing)|vibrant)\b",
        flags=re.IGNORECASE,
    ),
}


def authored_text(markdown: str) -> str:
    """Remove targets and code that are quoted rather than author prose."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`[^`]*`", "", text)
    return text


def validate(path: Path) -> Dict[str, object]:
    text = authored_text(path.read_text(encoding="utf-8"))
    violations: List[Dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                violations.append(
                    {
                        "line": line_number,
                        "rule": label,
                        "text": match.group(0),
                    }
                )
    return {
        "status": "pass" if not violations else "fail",
        "path": str(path),
        "violations": violations,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.input)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
