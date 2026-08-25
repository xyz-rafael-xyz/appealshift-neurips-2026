#!/usr/bin/env python3
"""Validate the AI for Peace form text and identify author-only gates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


AUTHOR_ACTION_REQUIRED = "AUTHOR_ACTION_REQUIRED"
FORMATS = {"Poster", "Talk", "Both"}
WORK_STATUSES = {"Work in progress", "Novel work", "Previously published work"}
PROHIBITED_STYLE = {
    "em_dash": "—",
    "semicolon": ";",
    "left_curly_quote": "“",
    "right_curly_quote": "”",
}


def validate(payload: Dict[str, object]) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    title = str(payload.get("title", ""))
    tldr = str(payload.get("tldr", ""))
    abstract = str(payload.get("abstract", ""))
    notes = str(payload.get("other_notes", ""))
    text_fields = {"title": title, "tldr": tldr, "abstract": abstract, "other_notes": notes}
    for field, value in text_fields.items():
        authored_value = re.sub(r"https?://\S+", "", value)
        if field != "other_notes" and not value.strip():
            errors.append(f"{field} is empty")
        for label, token in PROHIBITED_STYLE.items():
            if token in authored_value:
                errors.append(f"{field} contains {label}")
        if ":" in authored_value:
            errors.append(f"{field} contains a colon")
        if re.search(r"\bnot\s+[^.!?]{1,80}\bbut\b", authored_value, flags=re.IGNORECASE):
            errors.append(f"{field} contains a not-X-but-Y construction")
        if re.search(
            r"\b(?:not only|not just|neither\b[^.!?\n]{1,80}\bnor)\b",
            authored_value,
            flags=re.IGNORECASE,
        ):
            errors.append(f"{field} contains negative parallelism")
        if re.search(
            r",\s+[^,.\n]{1,80},\s+(?:and|or)\s+[^,.\n]{1,80}[.!?]",
            authored_value,
            flags=re.IGNORECASE,
        ):
            errors.append(f"{field} contains a serial three-part list")
        if re.search(
            r"\b(?:additionally|crucial|delve|pivotal|showcas(?:e|es|ed|ing)|"
            r"testament|tapestry|underscor(?:e|es|ed|ing)|vibrant)\b",
            authored_value,
            flags=re.IGNORECASE,
        ):
            errors.append(f"{field} contains stock promotional wording")
    if len(tldr) > 300:
        errors.append(f"TLDR has {len(tldr)} characters, above 300")
    if len(abstract) > 2500:
        errors.append(f"abstract has {len(abstract)} characters, above 2500")
    if len(notes) > 500:
        errors.append(f"other notes has {len(notes)} characters, above 500")
    if payload.get("presentation_format") not in FORMATS:
        errors.append("invalid presentation format")
    if payload.get("work_status") not in WORK_STATUSES:
        errors.append("invalid work status")
    if payload.get("work_status") == "Previously published work" and not str(
        payload.get("publication_venue", "")
    ).strip():
        errors.append("publication venue is required for previously published work")
    for field in ("presenter_names", "presenter_emails", "in_person_attendance"):
        value = payload.get(field)
        if value == AUTHOR_ACTION_REQUIRED:
            warnings.append(f"{field} requires author action")
        elif not value:
            errors.append(f"{field} is empty")
    required_phrases = {
        "synthetic disclosure": "synthetic",
        "humanitarian link": "humanitarian",
        "peace link": "peace",
    }
    lower_abstract = abstract.lower()
    for label, phrase in required_phrases.items():
        if phrase not in lower_abstract:
            errors.append(f"abstract lacks {label}")
    for claim in ("guarantee", "guaranteed acceptance", "real-world fairness"):
        if claim in lower_abstract:
            errors.append(f"abstract contains prohibited claim {claim}")
    return {
        "content_status": "pass" if not errors else "fail",
        "portal_ready": not errors and not warnings,
        "characters": {"title": len(title), "tldr": len(tldr), "abstract": len(abstract), "other_notes": len(notes)},
        "errors": errors,
        "author_only_gates": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = validate(payload)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if report["content_status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
