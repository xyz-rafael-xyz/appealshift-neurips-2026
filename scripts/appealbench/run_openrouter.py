#!/usr/bin/env python3
"""Run the two primary AppealShift conventions through OpenRouter."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.openrouter import complete, response_trace  # noqa: E402

from protocol import PROTOCOL_VERSION, initial_messages, prompt_hash, score_output  # noqa: E402
from run_mlx import append_jsonl, load_jsonl, sha256  # noqa: E402


CONDITIONS = ("independent_review", "prior_rationale")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def trace_cost(trace: Mapping[str, object]) -> float:
    usage = trace.get("usage") or {}
    value = usage.get("cost") if isinstance(usage, Mapping) else None
    if not isinstance(value, (int, float)):
        raise RuntimeError("OpenRouter response omitted numeric cost metadata")
    return float(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--max-cost-usd", type=float, default=2.0)
    args = parser.parse_args()
    rows = load_jsonl(args.input)
    existing = load_jsonl(args.output)
    completed = {(str(row["variant_id"]), str(row["condition"])) for row in existing}
    pending = [
        (row, condition)
        for row in rows
        for condition in CONDITIONS
        if (str(row["variant_id"]), condition) not in completed
    ]
    dataset_hash = sha256(args.input)
    started_utc = utc_now()
    total_cost = sum(float(row.get("cost_usd") or 0.0) for row in existing)

    def run(spec: tuple[dict[str, object], str]) -> dict[str, object]:
        row, condition = spec
        messages = initial_messages(row, condition)
        started = time.time()
        data = complete(
            args.model,
            messages,
            max_tokens=args.max_tokens,
            seed=args.seed,
            reasoning_effort="none",
        )
        trace = response_trace(data)
        cost = trace_cost(trace)
        trace["seconds"] = round(time.time() - started, 3)
        raw = str(data["choices"][0]["message"]["content"])
        return {
            "record_type": "appeal_review",
            "study_status": "post_audit_frontier_replication",
            "protocol_version": PROTOCOL_VERSION,
            "variant_id": row["variant_id"],
            "case_id": row["case_id"],
            "service_family": row["service_family"],
            "surface_form": row["surface_form"],
            "evidence_state": row["evidence_state"],
            "target_disposition": row["target_disposition"],
            "condition": condition,
            "model": args.model,
            "revision": args.revision,
            "dataset": str(args.input),
            "dataset_sha256": dataset_hash,
            "run_started_utc": started_utc,
            "completed_utc": utc_now(),
            "final_prompt_sha256": prompt_hash(messages),
            "raw_output": raw,
            "score": score_output(row, raw),
            "response_trace": trace,
            "cost_usd": cost,
            "runtime": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "backend": "OpenRouter chat completions",
                "requested_model": args.model,
                "seed": args.seed,
                "temperature": None,
                "reasoning_effort": "none",
                "max_tokens": args.max_tokens,
                "api_determinism_guaranteed": False,
            },
        }

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for start in range(0, len(pending), args.workers):
            if total_cost >= args.max_cost_usd:
                raise SystemExit(f"cost stop reached at ${total_cost:.4f}")
            batch = pending[start : start + args.workers]
            records = [future.result() for future in as_completed([pool.submit(run, spec) for spec in batch])]
            total_cost += sum(float(row["cost_usd"]) for row in records)
            append_jsonl(args.output, records)
            print(json.dumps({"completed": min(start + len(batch), len(pending)), "pending": len(pending), "cost_usd": round(total_cost, 6)}, sort_keys=True), flush=True)
    final = load_jsonl(args.output)
    expected = len(rows) * len(CONDITIONS)
    if len(final) != expected or len({(str(row["variant_id"]), str(row["condition"])) for row in final}) != expected:
        raise SystemExit("frontier AppealShift output is incomplete")
    print(json.dumps({"event": "complete", "records": len(final), "output": str(args.output), "sha256": sha256(args.output), "cost_usd": round(total_cost, 6)}, sort_keys=True))


if __name__ == "__main__":
    main()
