# AppealShift full results

## Primary matched-source experiment

The invalid-source extension contains 48 invalid-evidence semantic cases, two surface orders, four plausible but unlisted source types, two review conditions, and four model artifacts. The artifact also supplies the later matched-control protocol and its complete records. That control replaces each unlisted source with both accepted source types for the same 12 base requests, giving 24 valid semantic cases and 384 additional decisions. Together, the two source classes supply 1,152 reviews. The public artifact history does not establish when either protocol was written relative to generation. The earlier 3,072-review grid remains a wider secondary audit of four evidence states.

| Quantity | Independent review | Prior rationale |
|---|---:|---:|
| Decisions | 384 | 384 |
| Disposition accuracy | 0.00 percent | 6.25 percent |
| False eligibility | 51.56 percent | 60.42 percent |
| Fully grounded correctness | 0.00 percent | 0.00 percent |

The paired false-eligibility increase is 8.85 points with a descriptive interval from 7.29 to 10.42 after clustering the 20,000 bootstrap samples on the 12 base requests. The resampler computes 32 paired effects within each request and then draws 12 request-level means. All 12 observed means are positive and range from 3.125 to 12.5 points. Mistral supplies the entire increase, moving from 6.25 to 41.67 percent. Qwen and Gemma mark every record eligible under both conditions. Phi marks none eligible. Independent-review exact accuracy remains zero for every invalid-source type. Under rationale exposure, false eligibility is 51.04 percent for policy-first prompts and 69.79 percent for record-first prompts.

### Independent-review disposition matrix for unlisted sources

| Model | Eligible | Ineligible | Need information | Human review |
|---|---:|---:|---:|---:|
| Qwen3 4B | 96 | 0 | 0 | 0 |
| Gemma 3 4B | 96 | 0 | 0 | 0 |
| Mistral 7B | 6 | 0 | 90 | 0 |
| Phi-4-mini | 0 | 0 | 72 | 24 |

No model returns the required `INELIGIBLE` disposition. The zero exact score therefore pools three distinct behaviors. Qwen and Gemma accept every unlisted record. Mistral usually asks for information. Phi divides its answers between information requests and human review.

The target follows the fictional C2 rule and should not be read as a recommendation for real casework. A real service could define an unlisted but current-looking source as a reason to request accepted evidence. That policy would target `NEED_INFORMATION` instead. The benchmark keeps the printed mapping fixed so it can audit model adherence while leaving the normative service choice unresolved.

### Matched source discrimination under independent review

| Model | Valid sensitivity | Invalid specificity | Exact invalid accuracy | Balanced discrimination |
|---|---:|---:|---:|---:|
| Qwen3 4B | 100.0 | 0.0 | 0.0 | 50.0 |
| Gemma 3 4B | 100.0 | 0.0 | 0.0 | 50.0 |
| Mistral 7B | 77.1 | 93.8 | 0.0 | 85.4 |
| Phi-4-mini | 50.0 | 100.0 | 0.0 | 75.0 |

Sensitivity is acceptance of the 48 matched valid records. Specificity is any non-acceptance of the 96 matched unlisted records. Exact invalid accuracy still requires the policy's stated disposition. The controls show constant acceptance for Qwen and Gemma, partial source discrimination with wrong routing for Mistral, and overcautious routing for Phi. They prevent the invalid-only endpoint from rewarding a constant rejector.

The invalid dataset SHA-256 is `ee78160188f0dfc64ab77d38efa62fb704c2e0a3621ecd6e3692c863b5097a6b`. The matched valid-control SHA-256 is `103cd2bd2a2d1430d27b0f4a48753491a65d1850772d19f05940cdb94dc5eb2c`. All eight source-class model files passed complete-grid, revision, prompt and score validation.

## Integrity

The frozen evaluation contains 3,072 final reviews from four pinned models. Each model produced 768 reviews. Every model-condition-evidence-state cell contains 48 records. The complete validator found no provenance or score error. The primary scorer agreed with the independently written audit scorer on every record.

| Check | Result |
|---|---|
| Final reviews | 3,072 |
| Preliminary commitment calls | 768 |
| Complete model grids | 4 of 4 |
| Balanced cells | 64 of 64 at 48 records |
| Main and audit scorer disagreements | 0 |
| Unparsed final outputs | 8 of 3,072 |
| Independent result checks | 1,080 of 1,080 passed |
| Matched-source decisions | 1,152 |
| Matched valid-control decisions | 384 |

The score-blind audit packet selected 384 records across 128 strata. Selection used identifiers only. Its human review status remains `not_performed` because no external labels were collected.

A separate fixed five-case audit examines Phi outputs that have the correct prior-rationale disposition but fail grounding. All five cite the wrong policy clause, using C1, C3 or C4 instead of C2. One also omits the decisive evidence identifier E1. The complete records are in `validation/appealbench/phi_grounding_five_case_audit.json`.

## Confirmatory result

The directional hypothesis predicted that an earlier denial rationale would lower accuracy on valid appeals. The result went in the opposite direction.

| Quantity | Result |
|---|---|
| Independent valid accuracy | 83.85 percent, 161 of 192 |
| Prior-rationale valid accuracy | 90.62 percent, 174 of 192 |
| Paired difference | +6.77 percentage points |
| Clustered 95 percent interval | +4.17 to +9.90 points |
| Sign randomization result | p = 0.00046 |
| Semantic base cases | 24 |

Thirteen of the 192 model-by-surface pairs changed from an incorrect independent answer to a correct prior-rationale answer. None changed in the harmful direction on valid appeals. The descriptive paired counts agree with the clustered estimate, though they are not an independent inferential test.

The pooled gain came from one model. Mistral rose from 35 of 48 correct to 48 of 48. Qwen and Gemma were already perfect under independent review. Phi remained at 30 of 48.

| Model | Independent | Prior rationale | Paired difference | Clustered 95 percent interval |
|---|---|---|---|---|
| Qwen3 4B | 100.00 percent | 100.00 percent | 0.00 points | 0.00 to 0.00 |
| Phi-4-mini | 62.50 percent | 62.50 percent | 0.00 points | 0.00 to 0.00 |
| Gemma 3 4B | 100.00 percent | 100.00 percent | 0.00 points | 0.00 to 0.00 |
| Mistral 7B | 72.92 percent | 100.00 percent | +27.08 points | +16.67 to +39.58 |

The confirmatory effect therefore shows model-specific context sensitivity. It does not establish a general benefit from showing an earlier rationale.

The interval conditions on the four named model artifacts. It does not include uncertainty over a broader model population. Per-model results are primary, while the pooled result remains the prespecified fixed-artifact summary.

## Evidence-state tradeoffs

Prior-rationale exposure changed the error distribution outside the confirmatory valid state. These comparisons are exploratory.

| Evidence state | Independent accuracy | Prior-rationale accuracy | Main additional observation |
|---|---|---|---|
| Valid | 83.85 percent | 90.62 percent | Failure to correct fell from 16.15 to 9.38 percent |
| Invalid | 9.38 percent | 24.48 percent | False eligibility rose from 49.48 to 61.46 percent |
| Incomplete | 50.00 percent | 35.94 percent | Appropriate information requests fell by 14.06 points |
| Conflict | 11.46 percent | 13.54 percent | Appropriate human review rose by 2.08 points |

Invalid-case accuracy and invalid-case safety did not move together. Phi supplied most of the correct `INELIGIBLE` changes. Mistral introduced a separate false-eligibility problem, moving from 0 to 50 percent on that state. Qwen remained near universal false eligibility, while Gemma remained at 100 percent. This heterogeneity rules out a single account in which the prior rationale either helps or harms every model.

Across all evidence states, prior-rationale accuracy was 41.15 percent. Independent-review accuracy was 38.67 percent. Fully grounded correctness was 26.17 and 27.34 percent, respectively. The rationale improved schema validity from 79.30 to 87.11 percent even as evidence correctness fell from 79.04 to 73.96 percent.

Independent-review accuracy was only 9.38 percent on invalid records, and appropriate conflict routing was 11.46 percent. Those floor effects make the associated deltas unsuitable as evidence of task capability at this model scale. They remain useful as diagnostics of which wrong action appeared.

## Exploratory workflows

The evidence checklist did not produce a reliable overall accuracy gain over prior-rationale review. Its paired difference was -0.91 points with a clustered interval from -2.73 to +0.91. Valid-appeal accuracy was identical at 90.62 percent. On invalid evidence, the checklist reduced false eligibility by 2.08 points. That interval ran from -5.21 to +1.04, so the direction remains uncertain.

The commit-first workflow was adverse. Overall accuracy fell by 7.55 points relative to prior-rationale review, with an interval from -10.03 to -4.95. Valid accuracy fell by 3.12 points, with an interval from -5.21 to -1.04. False eligibility on invalid evidence rose by 10.42 points. Its interval ran from +6.77 to +13.54.

The final commit-first disposition differed from the preliminary answer in 194 of 768 reviews. Fifty-six changes were corrective under the target label. Fifty were harmful. The remaining changed answers moved between two incorrect dispositions. A preliminary commitment did not stabilize good reasoning in this setting.

## Surface-order sensitivity

The two surface forms preserve the same policy and evidence while changing whether the policy or record appears first. Models disagreed across those forms in 377 of 1,536 matched model-case-condition pairs, or 24.54 percent.

| Model | Surface disagreements | Rate over 384 pairs |
|---|---|---|
| Qwen3 4B | 11 | 2.86 percent |
| Gemma 3 4B | 31 | 8.07 percent |
| Mistral 7B | 140 | 36.46 percent |
| Phi-4-mini | 195 | 50.78 percent |

Surface order also changed pooled accuracy differently by workflow. Independent review favored record-first prompts by 12.76 points. The checklist favored policy-first prompts by 9.11 points. Commit-first review favored record-first prompts by 9.11 points. Prior-rationale review differed by 1.04 points. These are descriptive robustness findings.

All model-specific and state-specific intervals are exploratory. They are unadjusted, and no multiplicity correction was applied.

## Leave-one-model-out sensitivity

The fixed-artifact valid-appeal gain is 6.77 points. Removing Mistral reduces it to zero. Removing Phi produces 9.03 points. The same value follows when Qwen or Gemma is removed. Mistral therefore supplies the only positive model direction. Qwen and Gemma were already perfect under both conditions, while Phi remained unchanged at 62.50 percent.

## Same-case BF16 check

Qwen and Gemma were rerun with matching BF16 artifacts on all 48 valid-case surface variants under independent and prior-rationale review. This produced 192 new reviews and 384 matched four-bit plus BF16 records. Both models retained 100 percent disposition accuracy and full grounding in every precision-condition cell. Schema validity was also 100 percent. The check cannot identify a precision effect because each compared cell is at ceiling.

## Adversarial invalid slice

Twelve new invalid semantic cases used plausible unlisted sources and subtler continuity language in the earlier rationale. Both prompt orders and both review conditions produced 192 reviews across the four original artifacts. Independent-review accuracy was zero. Prior-rationale accuracy was 10.42 percent. False eligibility rose from 50.00 to 57.29 percent, while fully grounded correctness stayed at zero. This exploratory slice confirms that the invalid state remains floor-limited under harder wording.

## Interpretation

The earlier rationale did shape review, though it did not act like a uniform anchor to denial. For one model it corrected valid appeals. Elsewhere it changed which mistakes appeared, including more false eligibility under invalid evidence and fewer information requests under incomplete evidence.

The result supports a narrow practical recommendation. A prior rationale is an active input to model behavior even when the stated policy gives it no evidentiary status. A deployment audit should test matched cases across the evidence states that matter for the workflow. It should also retain meaning-preserving prompt variants. Aggregate accuracy alone would have hidden the adverse shifts observed here.

AppealShift remains a synthetic behavioral audit. It does not measure whether an institutional appeal is accessible or fair. It cannot establish legal compliance or effective remedy.
