# AppealShift reproducibility supplement

This archive supports the AI for Peace submission `Matched Sources Expose Distinct Admissibility Failures in Small-Model Appeal Review`. It contains synthetic cases, recorded raw generations, deterministic analyses, and validation evidence. It contains no model weights, personal data, or real humanitarian records.

## Contents

- `data/appealbench/` contains the development set, original evaluation, plausible unlisted sources and matched accepted-source controls.
- `experiments/appealbench/models.json` pins the four model revisions.
- `experiments/appealbench/development_v1/` preserves the first development run.
- `experiments/appealbench/development_v2/` contains the amended development run that passed the proceed gate.
- `experiments/appealbench/full/` contains the four complete evaluation runs.
- `experiments/appealbench/full_analysis/` contains the frozen result tables.
- `experiments/appealbench/full_error_analysis/` contains confusion and paired-transition tables.
- `experiments/appealbench/adversarial_v2/` contains the 768 primary decisions.
- `experiments/appealbench/adversarial_v2_analysis.json` contains the primary source, surface, model, and condition results.
- `experiments/appealbench/matched_valid_controls/` contains the 384 accepted-source reviews and the supplied control protocol. The public artifact history does not establish the protocol's timing.
- `experiments/appealbench/source_discrimination_analysis.json` contains the matched source cells, disposition matrix and 12-base-request bootstrap.
- `validation/appealbench/` contains dataset, run, claim, and package checks.
- `scripts/appealbench/` contains generation, scoring, analysis, plotting, and validation code.
- `reports/appealbench/EXPERIMENT_PROTOCOL.md` records the design and development amendment.
- `reports/appealbench/MATCHED_VALID_SOURCE_PROTOCOL.md` records the accepted-source control before generation.

Every named service, policy, request, record, and evidence item is fictional. Labels describe synthetic workflow fields rather than a real person or organization.

## Environment

Generation used Python 3.12 on Apple silicon with the versions in `supplement_requirements.txt`. MLX generation requires compatible Apple hardware. Dataset regeneration, scoring, analysis, and validation do not load model weights.

The model repository identifiers and immutable revisions appear in `experiments/appealbench/models.json`. Generation is greedy with an output limit of 180 tokens and batch size four.

## Core validation

Run these commands from the archive root.

```bash
PYTHONPATH=scripts/appealbench python -m unittest discover -s scripts/appealbench -p 'test_*.py'
python scripts/appealbench/validate_dataset.py \
  --evaluation data/appealbench/evaluation.jsonl \
  --development data/appealbench/development.jsonl \
  --output validation/appealbench/reproduced_dataset_validation.json
python scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/evaluation.jsonl \
  --runs \
    experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --output validation/appealbench/reproduced_full_validation.json
```

The run validator reconstructs every final prompt. It checks model revisions and dataset hashes, then recomputes stored scores with the main scorer. It also compares them with a separately implemented audit scorer.

Validate and analyze the primary plausible-source experiment with the commands below.

```bash
python scripts/appealbench/validate_adversarial_v2.py \
  --v2 data/appealbench/adversarial_v2.jsonl \
  --output validation/appealbench/reproduced_adversarial_v2_dataset_audit.json
python scripts/appealbench/validate_runs.py \
  --dataset data/appealbench/adversarial_v2.jsonl \
  --runs experiments/appealbench/adversarial_v2/qwen3.jsonl \
         experiments/appealbench/adversarial_v2/phi4mini.jsonl \
         experiments/appealbench/adversarial_v2/gemma3.jsonl \
         experiments/appealbench/adversarial_v2/mistral7b.jsonl \
  --conditions independent_review prior_rationale \
  --output validation/appealbench/reproduced_adversarial_v2_run_audit.json
python scripts/appealbench/analyze_adversarial_v2.py \
  --dataset data/appealbench/adversarial_v2.jsonl \
  --runs experiments/appealbench/adversarial_v2/qwen3.jsonl \
         experiments/appealbench/adversarial_v2/phi4mini.jsonl \
         experiments/appealbench/adversarial_v2/gemma3.jsonl \
         experiments/appealbench/adversarial_v2/mistral7b.jsonl \
  --output experiments/appealbench/reproduced_adversarial_v2_analysis.json
```

The dataset digest is `ee78160188f0dfc64ab77d38efa62fb704c2e0a3621ecd6e3692c863b5097a6b`. The complete-grid validator must report 96 rows per model-condition cell and zero scorer disagreements.

Regenerate the accepted-source dataset and joint analysis without calling a model.

```bash
python scripts/appealbench/generate_matched_valid_controls.py
python scripts/appealbench/analyze_source_discrimination.py \
  --invalid-runs experiments/appealbench/adversarial_v2/*.jsonl \
  --valid-runs experiments/appealbench/matched_valid_controls/*.jsonl
```

The accepted-source dataset digest is `103cd2bd2a2d1430d27b0f4a48753491a65d1850772d19f05940cdb94dc5eb2c`. The joint analysis requires 768 invalid-source and 384 accepted-source reviews. Its invalid-source interval clusters on the 12 base requests with seed `20260825` and 20,000 samples.

## Analysis

Regenerate the complete analysis with the frozen seed and resample count.

```bash
python scripts/appealbench/analyze.py \
  --runs \
    experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --output-dir experiments/appealbench/reproduced_analysis \
  --bootstrap-resamples 20000 \
  --randomization-draws 100000 \
  --seed 20260822
```

Regenerate the descriptive failure tables and main figure.

```bash
python scripts/appealbench/error_analysis.py \
  --runs \
    experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --output-dir experiments/appealbench/reproduced_error_analysis
python scripts/appealbench/plot_results.py \
  --analysis experiments/appealbench/reproduced_analysis/analysis.json \
  --png experiments/appealbench/reproduced_analysis/disposition_accuracy.png \
  --pdf experiments/appealbench/reproduced_analysis/disposition_accuracy.pdf
```

Run the independent claim checker after the combined run validator.

```bash
python scripts/appealbench/validate_result_claims.py \
  --runs \
    experiments/appealbench/full/qwen3.jsonl \
    experiments/appealbench/full/phi4mini.jsonl \
    experiments/appealbench/full/gemma3.jsonl \
    experiments/appealbench/full/mistral7b.jsonl \
  --analysis experiments/appealbench/full_analysis/analysis.json \
  --run-validation validation/appealbench/full_validation.json \
  --output validation/appealbench/reproduced_result_claim_validation.json
```

This checker does not import the main analysis. It recomputes the paired case effects, bootstrap interval, randomization p value, model directions, condition rates, state rates, parser counts, and source hashes.

## Audit packet

The release includes a score-blind stratified packet selected from model, condition, evidence-state, and surface-form cells. Its answer key is stored separately. The manifest records whether a human review occurred. A status of `not_performed` must not be described as external validation.

## Naming note

AppealShift is the public release name. The frozen internal protocol string and directory paths use `appealbench`. This preserves provenance after an unrelated computer-vision benchmark collision was discovered.

## Intended use

This supplement supports scientific review and reproduction. It is not a humanitarian decision tool. Do not use the cases or prompts to make decisions about people or access to services.
