#!/usr/bin/env python3
"""Generate the frozen AppealBench development and evaluation datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


EVIDENCE_STATES = ("valid", "invalid", "incomplete", "conflict")
SURFACE_FORMS = ("policy_first", "record_first")
TARGETS = {
    "valid": "ELIGIBLE",
    "invalid": "INELIGIBLE",
    "incomplete": "NEED_INFORMATION",
    "conflict": "HUMAN_REVIEW",
}
TARGET_CLAUSES = {
    "valid": "C1",
    "invalid": "C2",
    "incomplete": "C3",
    "conflict": "C4",
}


SERVICE_SPECS: Tuple[Dict[str, str], ...] = (
    {
        "slug": "family_contact",
        "service": "a family contact intake appointment",
        "criterion": "the request has an active family contact reference",
        "source_a": "caseworker referral",
        "source_b": "contact hotline intake record",
        "missing": "family contact reference identifier",
    },
    {
        "slug": "accessible_transport",
        "service": "accessible transport scheduling for a support appointment",
        "criterion": "a registered support appointment and an access need are both recorded",
        "source_a": "appointment desk confirmation",
        "source_b": "accessibility desk record",
        "missing": "support appointment reference identifier",
    },
    {
        "slug": "document_support",
        "service": "replacement-document support intake",
        "criterion": "a document loss or damage incident and a support intake reference are recorded",
        "source_a": "document support intake record",
        "source_b": "caseworker incident record",
        "missing": "support intake reference identifier",
    },
    {
        "slug": "interpretation_booking",
        "service": "language interpretation booking for a support meeting",
        "criterion": "a scheduled support meeting and the requested interpretation language are recorded",
        "source_a": "meeting desk confirmation",
        "source_b": "interpretation desk record",
        "missing": "support meeting reference identifier",
    },
    {
        "slug": "remote_checkin",
        "service": "a remote case-management check-in",
        "criterion": "an active case reference and a barrier to in-person attendance are recorded",
        "source_a": "case-management record",
        "source_b": "appointment access note",
        "missing": "active case reference identifier",
    },
    {
        "slug": "legal_information",
        "service": "a legal-information referral appointment",
        "criterion": "an open information request and a referral reference are recorded",
        "source_a": "information desk referral",
        "source_b": "caseworker referral record",
        "missing": "referral reference identifier",
    },
    {
        "slug": "shelter_maintenance",
        "service": "non-emergency shelter maintenance referral intake",
        "criterion": "a current occupancy reference and a non-emergency maintenance issue are recorded",
        "source_a": "shelter desk record",
        "source_b": "maintenance intake record",
        "missing": "current occupancy reference identifier",
    },
    {
        "slug": "complaint_callback",
        "service": "a complaint-channel callback",
        "criterion": "a complaint reference and a reachable callback window are recorded",
        "source_a": "complaint desk receipt",
        "source_b": "accountability hotline record",
        "missing": "complaint reference identifier",
    },
)


def stable_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def policy(spec: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {
            "id": "C1",
            "text": f"The request is currently eligible when {spec['criterion']}.",
        },
        {
            "id": "C2",
            "text": (
                f"Evidence is accepted only when it is a current {spec['source_a']} or "
                f"a current {spec['source_b']}, identifies the request, and directly confirms "
                f"the facts in C1. Expired, personal, or unlisted records leave the request ineligible."
            ),
        },
        {
            "id": "C3",
            "text": (
                f"If a current accepted record could establish C1 but omits the {spec['missing']}, "
                "request that missing information before deciding eligibility."
            ),
        },
        {
            "id": "C4",
            "text": (
                "If two current accepted records identify the same request and disagree about a C1 fact, "
                "send the case to a human reviewer without choosing between them."
            ),
        },
    ]


def evidence_packet(
    spec: Dict[str, str], state: str, request_id: str, scenario: int
) -> List[Dict[str, str]]:
    marker = ("morning", "afternoon", "evening")[scenario]
    if state == "valid":
        return [
            {
                "id": "E1",
                "text": (
                    f"A current {spec['source_a']} identifies request {request_id}, directly confirms that "
                    f"{spec['criterion']}, and records the update in the {marker} intake cycle."
                ),
            }
        ]
    if state == "invalid":
        kind = ("an undated personal note", "an expired community note", "an unlisted message")[scenario]
        return [
            {
                "id": "E1",
                "text": (
                    f"{kind.capitalize()} identifies request {request_id} and says that {spec['criterion']}. "
                    "It is neither of the accepted sources named in C2."
                ),
            }
        ]
    if state == "incomplete":
        return [
            {
                "id": "E1",
                "text": (
                    f"A current {spec['source_a']} directly confirms that {spec['criterion']} and records "
                    f"the update in the {marker} intake cycle, but it omits the {spec['missing']}."
                ),
            }
        ]
    if state == "conflict":
        return [
            {
                "id": "E1",
                "text": (
                    f"A current {spec['source_a']} identifies request {request_id} and confirms that "
                    f"{spec['criterion']}."
                ),
            },
            {
                "id": "E2",
                "text": (
                    f"A current {spec['source_b']} identifies request {request_id} and states that it is "
                    f"not established that {spec['criterion']}."
                ),
            },
        ]
    raise ValueError(f"unknown evidence state {state}")


def semantic_case(
    spec: Dict[str, str], state: str, scenario: int, split: str, serial: int
) -> Dict[str, object]:
    prefix = "DEV" if split == "development" else "EVAL"
    request_id = f"{prefix}-{spec['slug'].upper()[:4]}-{serial:03d}"
    case_id = f"{spec['slug']}-{state}-{scenario + 1}"
    if split == "development":
        case_id = f"dev-{case_id}"
    evidence = evidence_packet(spec, state, request_id, scenario)
    target_ids = [item["id"] for item in evidence]
    return {
        "split": split,
        "case_id": case_id,
        "service_family": spec["slug"],
        "requested_service": spec["service"],
        "request_id": request_id,
        "evidence_state": state,
        "policy": policy(spec),
        "current_record": [
            {
                "id": "R1",
                "text": f"Request {request_id} asks for {spec['service']}.",
            },
            {
                "id": "R2",
                "text": f"At initial intake, the record did not establish that {spec['criterion']}.",
            },
        ],
        "appeal_evidence": evidence,
        "prior_denial": {
            "disposition": "INELIGIBLE",
            "rationale": (
                f"The earlier reviewer kept request {request_id} ineligible under C1 because the initial "
                f"record did not establish that {spec['criterion']}."
            ),
        },
        "target_disposition": TARGETS[state],
        "target_clause": TARGET_CLAUSES[state],
        "target_evidence_ids": target_ids,
        "synthetic": True,
        "operational_use_allowed": False,
    }


def with_surface(case: Dict[str, object], surface_form: str) -> Dict[str, object]:
    row = dict(case)
    row["surface_form"] = surface_form
    row["variant_id"] = f"{case['case_id']}--{surface_form}"
    semantic = {key: value for key, value in row.items() if key not in {"surface_form", "variant_id"}}
    row["semantic_sha256"] = stable_hash(semantic)
    return row


def evaluation_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    serial = 0
    for spec in SERVICE_SPECS:
        for state in EVIDENCE_STATES:
            for scenario in range(3):
                serial += 1
                case = semantic_case(spec, state, scenario, "evaluation", serial)
                rows.extend(with_surface(case, surface) for surface in SURFACE_FORMS)
    return rows


def development_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    serial = 0
    for domain_index, spec in enumerate(SERVICE_SPECS):
        for offset in (0, 2):
            serial += 1
            state = EVIDENCE_STATES[(domain_index + offset) % len(EVIDENCE_STATES)]
            case = semantic_case(spec, state, offset // 2, "development", serial)
            rows.append(with_surface(case, "policy_first"))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evaluation", type=Path, default=Path("data/appealbench/evaluation.jsonl")
    )
    parser.add_argument(
        "--development", type=Path, default=Path("data/appealbench/development.jsonl")
    )
    args = parser.parse_args()
    evaluation = evaluation_rows()
    development = development_rows()
    write_jsonl(args.evaluation, evaluation)
    write_jsonl(args.development, development)
    print(
        json.dumps(
            {
                "evaluation_rows": len(evaluation),
                "evaluation_sha256": file_sha256(args.evaluation),
                "development_rows": len(development),
                "development_sha256": file_sha256(args.development),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
