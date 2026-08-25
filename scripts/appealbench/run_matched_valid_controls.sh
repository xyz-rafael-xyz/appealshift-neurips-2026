#!/usr/bin/env bash
set -euo pipefail

models=(
  "mlx-community/Qwen3-4B-Instruct-2507-4bit"
  "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
  "mlx-community/Phi-4-mini-instruct-mlx-4Bit"
  "mlx-community/gemma-3-text-4b-it-4bit"
)
revisions=(
  "50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"
  "a4b8f870474b0eb527f466a03fbc187830d271f5"
  "d848c30f6d5419b9892433cf6b1062626d15340e"
  "4f665a4c50ecfe4ecdc34056ab52fe3e3c4abf9e"
)
labels=("qwen3" "mistral7b" "phi4mini" "gemma3")

.venv/bin/python scripts/appealbench/generate_matched_valid_controls.py
mkdir -p experiments/appealbench/matched_valid_controls
for index in 0 1 2 3; do
  .venv/bin/python scripts/appealbench/run_mlx.py \
    --model "${models[$index]}" \
    --revision "${revisions[$index]}" \
    --input data/appealbench/matched_valid_controls.jsonl \
    --output "experiments/appealbench/matched_valid_controls/${labels[$index]}.jsonl" \
    --conditions independent_review prior_rationale \
    --batch-size 8 \
    --max-tokens 180
done

.venv/bin/python scripts/appealbench/analyze_source_discrimination.py \
  --invalid-runs experiments/appealbench/adversarial_v2/*.jsonl \
  --valid-runs experiments/appealbench/matched_valid_controls/*.jsonl
