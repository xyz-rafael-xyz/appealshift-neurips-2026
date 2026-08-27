#!/bin/sh
set -eu

PYTHON_BIN=${PYTHON_BIN:-python3}
export PYTHONPATH=scripts/appealbench

"$PYTHON_BIN" -m unittest discover -s scripts/appealbench -p 'test_*.py'
"$PYTHON_BIN" scripts/appealbench/validate_dataset.py \
  --evaluation data/appealbench/evaluation.jsonl \
  --development data/appealbench/development.jsonl \
  --output validation/appealbench/reproduced_dataset_validation.json
"$PYTHON_BIN" scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/evaluation.jsonl \
  --runs experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --output validation/appealbench/reproduced_full_validation.json
"$PYTHON_BIN" scripts/appealbench/analyze.py \
  --runs experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --output-dir experiments/appealbench/reproduced_analysis \
  --bootstrap-resamples 20000 \
  --randomization-draws 100000 \
  --seed 20260822
"$PYTHON_BIN" scripts/appealbench/validate_result_claims.py \
  --runs experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --analysis experiments/appealbench/reproduced_analysis/analysis.json \
  --run-validation validation/appealbench/reproduced_full_validation.json \
  --output validation/appealbench/reproduced_result_claim_validation.json
"$PYTHON_BIN" scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/adversarial_slice.jsonl \
  --runs experiments/appealbench/adversarial/qwen3.jsonl \
    experiments/appealbench/adversarial/phi4mini.jsonl \
    experiments/appealbench/adversarial/gemma3.jsonl \
    experiments/appealbench/adversarial/mistral7b.jsonl \
  --conditions independent_review prior_rationale \
  --output validation/appealbench/reproduced_adversarial_validation.json
"$PYTHON_BIN" scripts/appealbench/analyze_adversarial_slice.py \
  --runs experiments/appealbench/adversarial/qwen3.jsonl \
    experiments/appealbench/adversarial/phi4mini.jsonl \
    experiments/appealbench/adversarial/gemma3.jsonl \
    experiments/appealbench/adversarial/mistral7b.jsonl \
  --output experiments/appealbench/reproduced_adversarial_analysis.json
"$PYTHON_BIN" scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/bf16_confirmatory_subset.jsonl \
  --models experiments/appealbench/bf16_models.json \
  --runs experiments/appealbench/bf16/qwen3.jsonl \
    experiments/appealbench/bf16/gemma3.jsonl \
  --conditions independent_review prior_rationale \
  --output validation/appealbench/reproduced_bf16_validation.json
"$PYTHON_BIN" scripts/appealbench/analyze_bf16_replication.py \
  --four-bit experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
  --bf16 experiments/appealbench/bf16/qwen3.jsonl \
    experiments/appealbench/bf16/gemma3.jsonl \
  --output experiments/appealbench/reproduced_bf16_analysis.json
"$PYTHON_BIN" scripts/appealbench/validate_adversarial_v2.py \
  --v2 data/appealbench/adversarial_v2.jsonl \
  --output validation/appealbench/reproduced_adversarial_v2_dataset_audit.json
"$PYTHON_BIN" scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/adversarial_v2.jsonl \
  --runs experiments/appealbench/adversarial_v2/qwen3.jsonl \
    experiments/appealbench/adversarial_v2/phi4mini.jsonl \
    experiments/appealbench/adversarial_v2/gemma3.jsonl \
    experiments/appealbench/adversarial_v2/mistral7b.jsonl \
  --conditions independent_review prior_rationale \
  --output validation/appealbench/reproduced_adversarial_v2_run_audit.json
"$PYTHON_BIN" scripts/appealbench/analyze_adversarial_v2.py \
  --dataset data/appealbench/adversarial_v2.jsonl \
  --runs experiments/appealbench/adversarial_v2/qwen3.jsonl \
    experiments/appealbench/adversarial_v2/phi4mini.jsonl \
    experiments/appealbench/adversarial_v2/gemma3.jsonl \
    experiments/appealbench/adversarial_v2/mistral7b.jsonl \
  --output experiments/appealbench/reproduced_adversarial_v2_analysis.json
cmp experiments/appealbench/adversarial_v2_analysis.json experiments/appealbench/reproduced_adversarial_v2_analysis.json
"$PYTHON_BIN" scripts/appealbench/generate_matched_valid_controls.py
"$PYTHON_BIN" scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/matched_valid_controls.jsonl \
  --runs experiments/appealbench/matched_valid_controls/qwen3.jsonl \
    experiments/appealbench/matched_valid_controls/phi4mini.jsonl \
    experiments/appealbench/matched_valid_controls/gemma3.jsonl \
    experiments/appealbench/matched_valid_controls/mistral7b.jsonl \
  --conditions independent_review prior_rationale \
  --output validation/appealbench/reproduced_matched_valid_run_audit.json
"$PYTHON_BIN" scripts/appealbench/analyze_source_discrimination.py \
  --invalid-runs experiments/appealbench/adversarial_v2/qwen3.jsonl \
    experiments/appealbench/adversarial_v2/phi4mini.jsonl \
    experiments/appealbench/adversarial_v2/gemma3.jsonl \
    experiments/appealbench/adversarial_v2/mistral7b.jsonl \
  --valid-runs experiments/appealbench/matched_valid_controls/qwen3.jsonl \
    experiments/appealbench/matched_valid_controls/phi4mini.jsonl \
    experiments/appealbench/matched_valid_controls/gemma3.jsonl \
    experiments/appealbench/matched_valid_controls/mistral7b.jsonl \
  --output experiments/appealbench/reproduced_source_discrimination_analysis.json
cmp experiments/appealbench/source_discrimination_analysis.json experiments/appealbench/reproduced_source_discrimination_analysis.json
"$PYTHON_BIN" scripts/appealbench/analyze_dual_convention.py \
  --invalid-dir experiments/appealbench/adversarial_v2 \
  --valid-dir experiments/appealbench/matched_valid_controls \
  --output experiments/appealbench/reproduced_dual_convention_analysis.json
cmp experiments/appealbench/dual_convention_analysis.json experiments/appealbench/reproduced_dual_convention_analysis.json
