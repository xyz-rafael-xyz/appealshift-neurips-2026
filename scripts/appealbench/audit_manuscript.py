#!/usr/bin/env python3
"""Audit AppealShift LaTeX sources against workshop and prose constraints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FORBIDDEN_LITERAL = {
    "em_dash": "—",
    "colon": ":",
    "semicolon": ";",
}

FORBIDDEN_PATTERNS = {
    "not_x_but_y": re.compile(r"\bnot\b[^.\n]{0,100}\bbut\b", re.IGNORECASE),
    "negative_parallelism": re.compile(
        r"\b(?:not only|not just|neither\b[^.!?\n]{1,80}\bnor)\b", re.IGNORECASE
    ),
    "serial_triplet": re.compile(
        r",\s+[^,.\n]{1,80},\s+(?:and|or)\s+[^,.\n]{1,80}[.!?]",
        re.IGNORECASE,
    ),
    "stock_transition": re.compile(
        r"\b(additionally|moreover|furthermore|in conclusion|it is worth noting|"
        r"it is important to note|this underscores|this highlights)\b",
        re.IGNORECASE,
    ),
    "inflated_claim": re.compile(
        r"\b(groundbreaking|revolutionary|transformative|unprecedented|"
        r"paradigm shift|game.changing|crucial|pivotal)\b",
        re.IGNORECASE,
    ),
    "priority_claim": re.compile(
        r"\b(first|novel)\s+(benchmark|dataset|study|work|evaluation|method|system)\b",
        re.IGNORECASE,
    ),
    "layout_override": re.compile(
        r"\\(?:usepackage\{geometry\}|geometry\{|vspace\{-|setlength\{\\text|titlespacing)",
        re.IGNORECASE,
    ),
}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=Path("papers/appealshift/paper.tex"))
    parser.add_argument("--abstract", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8")
    authored = re.sub(r"^\\workshoptitle\{AI for Peace Workshop\}\s*$", "", text, flags=re.MULTILINE)
    authored = re.sub(r"https?://[^}\s]+", "", authored)
    findings = []

    for name, literal in FORBIDDEN_LITERAL.items():
        for match in re.finditer(re.escape(literal), authored):
            findings.append({"rule": name, "line": line_number(authored, match.start())})

    for name, pattern in FORBIDDEN_PATTERNS.items():
        for match in pattern.finditer(authored):
            findings.append(
                {
                    "rule": name,
                    "line": line_number(authored, match.start()),
                    "text": " ".join(match.group(0).split())[:120],
                }
            )

    required = {
        "single_blind_workshop": r"\usepackage[sglblindworkshop]{template/neurips_2026}",
        "workshop_title": r"\workshoptitle{AI for Peace Workshop}",
        "paper_title": r"\title{Matched Source Controls Expose a Capability Boundary in Appeal Review}",
        "identified_author": r"\author{Rafael Gardos\\\texttt{gardos.rafael@gmail.com}}",
        "line_numbers_disabled": r"\nolinenumbers",
    }
    if not args.abstract:
        required["bibliography"] = r"\bibliography{references}"
        required["reproducibility_timing_boundary"] = (
            "The public history does not establish when any protocol or analysis plan "
            "was written relative to generation."
        )
        required["fixture_lineage_rule"] = (
            "A source audit found no appeal item or saved model review reused elsewhere."
        )
    missing = [name for name, literal in required.items() if literal not in text]

    if args.abstract and r"\bibliography" in text:
        findings.append({"rule": "abstract_has_bibliography", "line": 0})
    if not args.abstract:
        for forbidden_claim in (
            "1e3cd83",
            "46239112",
            "preserves the protocol and output chronology",
            "committed and pushed as",
            "Repository-recorded plausible-source experiment",
        ):
            if forbidden_claim in text:
                findings.append({
                    "rule": "unverifiable_public_history_claim",
                    "line": line_number(text, text.index(forbidden_claim)),
                    "text": forbidden_claim,
                })

    report = {
        "file": str(args.path),
        "forbidden_findings": findings,
        "missing_required_fields": missing,
        "pass": not findings and not missing,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
