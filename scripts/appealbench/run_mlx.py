#!/usr/bin/env python3
"""Run frozen AppealBench prompts with a pinned MLX model."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from jinja2.exceptions import TemplateError
except ModuleNotFoundError:
    class TemplateError(Exception):
        """Fallback used by dependency-light runner tests."""

try:
    import mlx
    from mlx_lm import batch_generate, load
    from mlx_lm.sample_utils import make_sampler
except ModuleNotFoundError:
    mlx = None
    batch_generate = None
    load = None
    make_sampler = None

from protocol import (
    CONDITIONS,
    PROTOCOL_VERSION,
    final_commit_messages,
    initial_messages,
    prompt_hash,
    score_output,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
        handle.flush()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fold_system_into_first_user(
    messages: Sequence[Dict[str, str]],
) -> List[Dict[str, str]]:
    if (
        len(messages) < 2
        or messages[0].get("role") != "system"
        or messages[1].get("role") != "user"
    ):
        raise ValueError("cannot fold system role without an initial system-user pair")
    return [
        {
            "role": "user",
            "content": f"{messages[0]['content']}\n\n{messages[1]['content']}",
        },
        *[dict(message) for message in messages[2:]],
    ]


def apply_template(
    tokenizer, messages: Sequence[Dict[str, str]]
) -> Tuple[List[int], str]:
    if getattr(tokenizer, "chat_template", None):
        adapter = "native_system_role"
        try:
            tokens = tokenizer.apply_chat_template(
                list(messages),
                tokenize=True,
                add_generation_prompt=True,
                return_dict=False,
            )
        except TemplateError:
            tokens = tokenizer.apply_chat_template(
                fold_system_into_first_user(messages),
                tokenize=True,
                add_generation_prompt=True,
                return_dict=False,
            )
            adapter = "system_folded_into_first_user"
        if hasattr(tokens, "tolist"):
            tokens = tokens.tolist()
        return list(tokens), adapter
    plain = "\n\n".join(f"{item['role'].upper()}: {item['content']}" for item in messages)
    tokens = tokenizer.encode(plain)
    if hasattr(tokens, "tolist"):
        tokens = tokens.tolist()
    return list(tokens), "plain_role_transcript"


def batch_generate_text(
    model,
    tokenizer,
    message_batches: Sequence[Sequence[Dict[str, str]]],
    max_tokens: int,
) -> Tuple[List[str], Dict[str, object]]:
    prepared = [apply_template(tokenizer, messages) for messages in message_batches]
    response = batch_generate(
        model,
        tokenizer,
        [tokens for tokens, _ in prepared],
        max_tokens=max_tokens,
        verbose=True,
        sampler=make_sampler(temp=0.0),
    )
    stats = response.stats
    return list(response.texts), {
        "prompt_tokens": int(stats.prompt_tokens),
        "prompt_tps": float(stats.prompt_tps),
        "generation_tokens": int(stats.generation_tokens),
        "generation_tps": float(stats.generation_tps),
        "peak_memory_gb": float(stats.peak_memory),
        "chat_template_adapters": sorted({adapter for _, adapter in prepared}),
    }


def runtime_record() -> Dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "mlx": getattr(mlx, "__version__", "unknown"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "decoding": "greedy",
        "temperature": 0.0,
    }


def make_record(
    row: Dict[str, object],
    condition: str,
    raw: str,
    final_messages: Sequence[Dict[str, str]],
    final_stats: Dict[str, object],
    model_id: str,
    revision: str,
    dataset_path: Path,
    dataset_hash: str,
    started_utc: str,
    preliminary_raw: str | None = None,
    preliminary_messages: Sequence[Dict[str, str]] | None = None,
    preliminary_stats: Dict[str, object] | None = None,
) -> Dict[str, object]:
    preliminary_score = None
    if preliminary_raw is not None:
        preliminary_score = score_output(row, preliminary_raw)
    final_score = score_output(row, raw)
    update = None
    if preliminary_score is not None:
        update = {
            "changed_disposition": preliminary_score["disposition"] != final_score["disposition"],
            "corrective_update": (
                not preliminary_score["disposition_correct"] and final_score["disposition_correct"]
            ),
            "harmful_update": (
                preliminary_score["disposition_correct"] and not final_score["disposition_correct"]
            ),
        }
    return {
        "record_type": "appeal_review",
        "protocol_version": PROTOCOL_VERSION,
        "variant_id": row["variant_id"],
        "case_id": row["case_id"],
        "service_family": row["service_family"],
        "surface_form": row["surface_form"],
        "evidence_state": row["evidence_state"],
        "target_disposition": row["target_disposition"],
        "condition": condition,
        "model": model_id,
        "revision": revision,
        "dataset": str(dataset_path),
        "dataset_sha256": dataset_hash,
        "run_started_utc": started_utc,
        "completed_utc": utc_now(),
        "final_prompt_sha256": prompt_hash(final_messages),
        "raw_output": raw,
        "score": final_score,
        "batch_stats": final_stats,
        "preliminary_prompt_sha256": (
            prompt_hash(preliminary_messages) if preliminary_messages is not None else None
        ),
        "preliminary_raw_output": preliminary_raw,
        "preliminary_score": preliminary_score,
        "preliminary_batch_stats": preliminary_stats,
        "update": update,
        "runtime": runtime_record(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument(
        "--input", type=Path, default=Path("data/appealbench/evaluation.jsonl")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS)
    )
    args = parser.parse_args()
    if args.batch_size < 1 or args.max_tokens < 1:
        raise SystemExit("batch size and max tokens must be positive")
    rows = load_jsonl(args.input)
    if args.limit > 0:
        rows = rows[: args.limit]
    output = args.output or Path("experiments/appealbench/raw") / f"{slugify(args.model)}.jsonl"
    existing = load_jsonl(output)
    completed = {
        (str(record.get("variant_id")), str(record.get("condition"))) for record in existing
    }
    pending = [
        (row, condition)
        for row in rows
        for condition in args.conditions
        if (str(row["variant_id"]), condition) not in completed
    ]
    dataset_hash = sha256(args.input)
    started_utc = utc_now()
    print(
        json.dumps(
            {
                "event": "load_model",
                "model": args.model,
                "revision": args.revision,
                "dataset_rows": len(rows),
                "records_pending": len(pending),
                "dataset_sha256": dataset_hash,
                "output": str(output),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    load_started = time.time()
    model, tokenizer = load(args.model, revision=args.revision)
    print(
        json.dumps({"event": "model_ready", "seconds": time.time() - load_started}),
        flush=True,
    )
    completed_count = len(existing)
    for offset in range(0, len(pending), args.batch_size):
        batch = pending[offset : offset + args.batch_size]
        initial = [initial_messages(row, condition) for row, condition in batch]
        first_outputs, first_stats = batch_generate_text(
            model, tokenizer, initial, max_tokens=args.max_tokens
        )
        final_outputs = list(first_outputs)
        final_messages = list(initial)
        final_stats: List[Dict[str, object]] = [first_stats] * len(batch)
        preliminary_outputs: List[str | None] = [None] * len(batch)
        preliminary_messages: List[Sequence[Dict[str, str]] | None] = [None] * len(batch)
        preliminary_stats: List[Dict[str, object] | None] = [None] * len(batch)

        commit_indices = [
            index for index, (_, condition) in enumerate(batch) if condition == "commit_then_review"
        ]
        if commit_indices:
            commit_messages = [
                final_commit_messages(batch[index][0], first_outputs[index])
                for index in commit_indices
            ]
            commit_outputs, commit_stats = batch_generate_text(
                model, tokenizer, commit_messages, max_tokens=args.max_tokens
            )
            for local_index, batch_index in enumerate(commit_indices):
                preliminary_outputs[batch_index] = first_outputs[batch_index]
                preliminary_messages[batch_index] = initial[batch_index]
                preliminary_stats[batch_index] = first_stats
                final_outputs[batch_index] = commit_outputs[local_index]
                final_messages[batch_index] = commit_messages[local_index]
                final_stats[batch_index] = commit_stats

        records = []
        for index, ((row, condition), raw) in enumerate(zip(batch, final_outputs)):
            records.append(
                make_record(
                    row=row,
                    condition=condition,
                    raw=raw,
                    final_messages=final_messages[index],
                    final_stats=final_stats[index],
                    model_id=args.model,
                    revision=args.revision,
                    dataset_path=args.input,
                    dataset_hash=dataset_hash,
                    started_utc=started_utc,
                    preliminary_raw=preliminary_outputs[index],
                    preliminary_messages=preliminary_messages[index],
                    preliminary_stats=preliminary_stats[index],
                )
            )
        append_jsonl(output, records)
        completed_count += len(records)
        print(
            json.dumps(
                {
                    "event": "progress",
                    "completed_total": completed_count,
                    "newly_completed": len(records),
                    "remaining": len(pending) - min(offset + args.batch_size, len(pending)),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    print(
        json.dumps(
            {
                "event": "complete",
                "output": str(output),
                "records": len(load_jsonl(output)),
                "output_sha256": sha256(output),
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
