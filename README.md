# AppealShift

This repository contains the synthetic cases, raw generations, scoring code, and analysis for the paper `Matched Sources Expose Distinct Admissibility Failures in Small-Model Appeal Review`.

The primary experiment pairs accepted records with administratively plausible records from unlisted sources. It tests whether four small model artifacts can discriminate the source classes under an explicit whitelist. It also measures how an earlier denial rationale changes the error pattern.

## One-command reproduction

Create a Python 3.12 environment, install `requirements.txt`, then run the command below from the repository root.

```bash
./reproduce.sh
```

The command checks the frozen datasets and raw runs, rebuilds the main analysis, checks every reported result, and rebuilds the two post-freeze robustness analyses. It does not download model weights or repeat inference.

## Dataset SHA-256 values

| File | SHA-256 |
|---|---|
| `data/appealbench/development.jsonl` | `551e1040dbe6d6fd9f365d4267115eb124fa2a7a6a2c2740b728de5554038a24` |
| `data/appealbench/evaluation.jsonl` | `5a7a74533c614dcdd244003bf9411d883237daac818731625d3229ea4c7ee9cf` |
| `data/appealbench/adversarial_slice.jsonl` | `1bc15b7082ebcc95a8851f6e0d110a1ed7d4d51477052778d73687271aa86e36` |
| `data/appealbench/adversarial_v2.jsonl` | `ee78160188f0dfc64ab77d38efa62fb704c2e0a3621ecd6e3692c863b5097a6b` |
| `data/appealbench/matched_valid_controls.jsonl` | `103cd2bd2a2d1430d27b0f4a48753491a65d1850772d19f05940cdb94dc5eb2c` |
| `data/appealbench/bf16_confirmatory_subset.jsonl` | `ba26a9f171d892f3c358db30149d035d1c4f7fcd3cf9e25a98c7725d6b0fbf3c` |

## Pinned model revisions

| Artifact | Revision |
|---|---|
| `mlx-community/Qwen3-4B-Instruct-2507-4bit` | `50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b` |
| `mlx-community/Phi-4-mini-instruct-mlx-4Bit` | `d848c30f6d5419b9892433cf6b1062626d15340e` |
| `mlx-community/gemma-3-text-4b-it-4bit` | `4f665a4c50ecfe4ecdc34056ab52fe3e3c4abf9e` |
| `mlx-community/Mistral-7B-Instruct-v0.3-4bit` | `a4b8f870474b0eb527f466a03fbc187830d271f5` |
| `mlx-community/Qwen3-4B-Instruct-2507-bf16` | `f9e77d4283734966e9cd641bf35547f0cff5d427` |
| `mlx-community/gemma-3-4b-it-bf16` | `665e04d28e93290c77b7832307606f7e87bb7616` |

## Expected runtime

Reproduction from the included raw outputs took 11.5 seconds on the 2021 M1 Pro machine used for the study. Memory use remains below 2 GB. Repeating inference requires Apple silicon with MLX and takes much longer.

## Package versions

The analysis was run with Python 3.12.13, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, Matplotlib 3.11.1, MLX 0.32.1, and mlx-lm 0.31.3. `requirements.txt` records the installable environment.

## Result map

The legacy directory name `experiments/appealbench/adversarial_v2/` maps to the paper's primary plausible-source experiment. Its four files contain 768 decisions. The matched accepted-source controls add 384 decisions under `experiments/appealbench/matched_valid_controls/`. Their joint analysis and disposition matrix are in `experiments/appealbench/source_discrimination_analysis.json`. The files under `experiments/appealbench/full/` contain the earlier four-state evaluation. Its paired analysis and leave-one-model-out table are under `experiments/appealbench/full_analysis/`. The twelve-case slice that motivated the primary extension is under `experiments/appealbench/adversarial/`. The same-model BF16 check is under `experiments/appealbench/bf16/`.

All cases and organizations are fictional. The benchmark is meant for research on review procedures. It must not be used to decide access to services.

## Literature boundary

Prior work establishes appeal prediction and rationale effects. AppealShift uses matched accepted and unlisted sources under an explicit fictional policy. It shows or hides an earlier denial rationale while keeping the current evidence and policy fixed. The contribution is the source-whitelist audit and its paired context comparison, not a general claim about humanitarian appeals.

## License

Code is released under the MIT License. The synthetic data and documentation are released under CC BY 4.0. The manuscript remains under the author's copyright.

## Fixture lineage

A source audit found no appeal item or saved model review reused elsewhere. Similar service families are topic overlap.
