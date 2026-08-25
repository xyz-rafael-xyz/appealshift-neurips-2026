#!/usr/bin/env python3
"""Independent AppealBench scorer used to audit the primary implementation."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple


VALID_DECISIONS = {
    "ELIGIBLE",
    "INELIGIBLE",
    "NEED_INFORMATION",
    "HUMAN_REVIEW",
}
REQUIRED_FIELDS = {"disposition", "policy_clause", "evidence_ids", "reply"}


def extract_object(text: str) -> Tuple[Dict[str, object] | None, str]:
    stripped = text.strip()
    try:
        candidate = json.loads(stripped)
    except json.JSONDecodeError:
        candidate = None
    if isinstance(candidate, dict):
        return candidate, "strict"
    snippets = [
        match.group(1)
        for match in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.I | re.S)
    ]
    left = text.find("{")
    right = text.rfind("}")
    if left != -1 and right > left:
        snippets.append(text[left : right + 1])
    for snippet in snippets:
        try:
            candidate = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate, "recovered"
    return None, "unparsed"


def audit_score(case: Dict[str, object], text: str) -> Dict[str, object]:
    obj, mode = extract_object(text)
    decision = None
    clause = None
    cited: List[str] = []
    reply = ""
    exact_fields = False
    valid_types = False
    if obj is not None:
        raw_decision = obj.get("disposition")
        raw_clause = obj.get("policy_clause")
        raw_cited = obj.get("evidence_ids")
        raw_reply = obj.get("reply")
        decision = raw_decision.strip().upper() if isinstance(raw_decision, str) else None
        clause = raw_clause.strip().upper() if isinstance(raw_clause, str) else None
        if isinstance(raw_cited, list) and all(isinstance(value, str) for value in raw_cited):
            cited = [value.strip().upper() for value in raw_cited]
        reply = raw_reply if isinstance(raw_reply, str) else ""
        exact_fields = set(obj.keys()) == REQUIRED_FIELDS
        valid_types = (
            isinstance(raw_decision, str)
            and isinstance(raw_clause, str)
            and isinstance(raw_cited, list)
            and all(isinstance(value, str) for value in raw_cited)
            and isinstance(raw_reply, str)
        )

    clause_universe = {str(entry["id"]).upper() for entry in case["policy"]}
    evidence_universe = {str(entry["id"]).upper() for entry in case["appeal_evidence"]}
    valid_schema = bool(
        obj is not None
        and exact_fields
        and valid_types
        and decision in VALID_DECISIONS
        and clause in clause_universe
        and len(cited) == len(set(cited))
        and set(cited).issubset(evidence_universe)
        and reply.strip()
    )
    correct_decision = decision == str(case["target_disposition"])
    correct_clause = clause == str(case["target_clause"])
    correct_evidence = set(cited) == {str(value) for value in case["target_evidence_ids"]}
    unknown = set(cited).difference(evidence_universe)
    if clause is not None and clause not in clause_universe:
        unknown.add(clause)
    target = str(case["target_disposition"])
    return {
        "parser_mode": mode,
        "schema_valid": valid_schema,
        "strict_format": mode == "strict" and valid_schema,
        "exact_keys": exact_fields,
        "disposition": decision,
        "policy_clause": clause,
        "evidence_ids": cited,
        "reply": reply,
        "reply_characters": len(reply),
        "reply_words": len(reply.split()),
        "unsupported_identifiers": sorted(unknown),
        "disposition_correct": correct_decision,
        "clause_correct": correct_clause,
        "evidence_correct": correct_evidence,
        "fully_grounded": bool(
            valid_schema and correct_decision and correct_clause and correct_evidence
        ),
        "failure_to_correct": target == "ELIGIBLE" and decision != "ELIGIBLE",
        "false_eligibility": target == "INELIGIBLE" and decision == "ELIGIBLE",
        "appropriate_information_request": (
            target == "NEED_INFORMATION" and decision == "NEED_INFORMATION"
        ),
        "appropriate_human_review": target == "HUMAN_REVIEW" and decision == "HUMAN_REVIEW",
    }
