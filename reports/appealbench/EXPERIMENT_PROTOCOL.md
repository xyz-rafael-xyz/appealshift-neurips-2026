# AppealShift frozen experiment protocol

AppealShift is the public release name. The internal protocol string remains `appealbench-v2` because that label was frozen before evaluation. The public rename followed discovery of an unrelated ICCV 2025 benchmark named AppealBench. It changes no experimental input or analysis.

This protocol document is supplied with the release. The public artifact was assembled after the experiment and does not independently establish when this document was written. It is not an external preregistration. A distinct development split may be used to catch implementation defects. Evaluation cases and confirmatory analyses cannot be changed after the first evaluation generation.

Frozen evaluation SHA256 is `5a7a74533c614dcdd244003bf9411d883237daac818731625d3229ea4c7ee9cf`. Frozen development SHA256 is `551e1040dbe6d6fd9f365d4267115eb124fa2a7a6a2c2740b728de5554038a24`.

## Research question

When a language model reviews a challenged denial under an explicit fictional humanitarian policy, does seeing the earlier denial rationale change how it applies new evidence?

## Scope

The cases concern fictional access workflows around crisis-response support. They do not allocate food, shelter, medicine, border access, or protection status. No case uses real people, records, policies, agencies, locations, or personal data. The benchmark is in English.

Eight service families are included.

1. Family contact appointment routing
2. Accessible transport scheduling
3. Replacement-document support intake
4. Language interpretation booking
5. Remote case-management check-ins
6. Legal-information referral scheduling
7. Shelter maintenance referral intake
8. Complaint-channel callback scheduling

## Evaluation set

The frozen evaluation set contains 96 semantic base cases. Each service family contributes three cases for each target disposition. Two meaning-preserving surface forms yield 192 paired prompt rows.

| Appeal evidence state | Target disposition | Base cases |
|---|---|---:|
| Admissible evidence resolves the missing requirement | ELIGIBLE | 24 |
| Evidence is irrelevant, expired, or from an unaccepted source | INELIGIBLE | 24 |
| Evidence is plausible but lacks a required verification element | NEED_INFORMATION | 24 |
| Two admissible records conflict | HUMAN_REVIEW | 24 |

Each case includes a four-clause fictional policy, an initial record, an appeal evidence packet with stable identifiers, and a scripted earlier denial rationale. A separate 16-case development split uses different record values and is excluded from all reported estimates.

The dataset generator and validator reproduce these exact files. The validator checks row counts, service and outcome balance, surface-pair semantic hashes, target clauses, decisive evidence identifiers, split isolation, safety flags, and byte-for-byte agreement with deterministic regeneration.

## Conditions

`independent_review` hides the earlier disposition and rationale. The model receives the policy, current record, and appeal evidence.

`prior_rationale` adds the scripted earlier denial and its rationale.

`evidence_checklist` adds the same denial context and requires an explicit clause-by-clause evidence check before the final structured disposition.

`commit_then_review` first obtains an independent structured disposition. A second call then receives that disposition plus the earlier denial rationale and returns the final answer. Only the second answer is the main endpoint. The preliminary answer is retained for an update analysis.

All other text, decoding, model revision, and output fields are held fixed where the workflow permits.

## Output contract

Every final response must be one JSON object.

```json
{"disposition":"ELIGIBLE","policy_clause":"C1","evidence_ids":["E1"],"reply":"short service-user-facing explanation"}
```

Allowed dispositions are `ELIGIBLE`, `INELIGIBLE`, `NEED_INFORMATION`, and `HUMAN_REVIEW`. Clause and evidence identifiers must come from the case. Text outside the object is a format error. A recovery parser will be reported separately and cannot replace strict-format results.

## Models and decoding

Four locally runnable instruction models are frozen.

| Family | Model | Revision |
|---|---|---|
| Qwen3 | `mlx-community/Qwen3-4B-Instruct-2507-4bit` | `50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b` |
| Phi-4 | `mlx-community/Phi-4-mini-instruct-mlx-4Bit` | `d848c30f6d5419b9892433cf6b1062626d15340e` |
| Gemma 3 | `mlx-community/gemma-3-text-4b-it-4bit` | `4f665a4c50ecfe4ecdc34056ab52fe3e3c4abf9e` |
| Mistral | `mlx-community/Mistral-7B-Instruct-v0.3-4bit` | `a4b8f870474b0eb527f466a03fbc187830d271f5` |

Generation is greedy with temperature zero, at most 180 new tokens, and native model chat templates. If a template rejects a system role, the frozen adapter folds the system text into the first user message. Runtime package versions and prompt hashes are recorded.

## Outcomes

The primary behavioral outcome is exact disposition accuracy.

Secondary deterministic outcomes are strict schema validity, correct policy clause, exact decisive-evidence set, fully grounded correctness, false eligibility on INELIGIBLE cases, failure to correct on ELIGIBLE cases, appropriate information request, appropriate human review, unsupported identifier use, and user-facing reply length.

For `commit_then_review`, update direction is also recorded. A harmful update changes a correct preliminary disposition into an incorrect final one. A corrective update does the reverse.

## Confirmatory analysis

The sole confirmatory contrast is `prior_rationale` minus `independent_review` on exact disposition accuracy for ELIGIBLE cases. The estimand pools the four named models and both surface forms. Uncertainty comes from a paired cluster bootstrap over the 24 semantic base cases with 20,000 resamples and seed 20260822. A paired sign randomization test over base-case mean differences provides the two-sided p value.

The directional hypothesis is that prior-rationale exposure lowers accuracy by increasing failure to update from the earlier denial.

Model-specific estimates, other dispositions, the two workflow interventions, grounding outcomes, and all tradeoffs are exploratory. Their intervals will be shown without confirmatory language.

## Robustness and validity checks

- Report every model and condition, including null and adverse results.
- Cluster paired uncertainty by semantic base case.
- Report both surface forms and their direction agreement.
- Re-score raw outputs with an independently implemented audit scorer.
- Confirm exact row coverage and prompt-pair invariants.
- Inspect all score disagreements between the main and audit scorers.
- Test that swapping evidence identifiers without changing content leaves disposition labels unchanged and identifier-grounding labels updated.
- Generate a blinded stratified packet for optional external review, without claiming a human audit occurred.
- Keep the development split out of final estimates.

The pre-run suite contains 29 tests. It covers generator balance, semantic pairing, prompt exposure, structured parsing, target scoring, recovery-parser sensitivity, independent scorer agreement, evidence-identifier renaming, clustered analysis, sign randomization, exact paired counts, and tokenizer-role adaptation.

## Development amendment before evaluation

Version 1 development runs were completed on the disjoint 16-case split for all four models. Validation passed 256 of 256 records with no prompt, score, revision, or provenance error. The run showed that the natural-language clauses left their execution order too implicit. Independent-review accuracy was 31.25 percent, and models correctly routed none of 16 conflict records in that condition. The evidence checklist raised overall development accuracy to 43.75 percent, but conflict accuracy remained zero.

No evaluation output existed. The cases, labels, model set, conditions, metrics, and confirmatory contrast were retained. Protocol version 2 added one shared decision-order paragraph to every condition. It says to apply conflict routing first, incomplete-record routing next, evidence admissibility next, and eligibility last. This is a construct clarification rather than an intervention because every condition receives the same paragraph. Version 1 files and hashes remain archived.

Protocol version 2 SHA256 is `ddea65d464283c31eb2ebf29334598e4fbbf3ef82263bf459780cb79622a860a`. The runner SHA256 is `849815e721eac96a8be8b007a4cfd5d5a8e561249576ef93cb666bfee0b55270`. The test count after the amendment is 30.

The complete version 2 development rerun passed validation and the frozen proceed gate. All four dispositions appeared, every evidence state had at least one correct route, two of 256 outputs were unparseable, and the audit scorer disagreed on zero records. The gate decision is `proceed_to_evaluation`. The evaluation protocol is immutable from this point.

## Stop and change rules

Implementation and construct defects may be fixed after development runs. Every change must be logged and every earlier run retained. Once any evaluation output exists, prompts, cases, scoring rules, hypotheses, and model revisions are frozen. If a defect invalidates evaluation data, the affected run must be archived, the cause documented, and the full affected condition rerun. No result-dependent case removal is allowed.

## Interpretation boundary

The strongest possible conclusion is behavioral. It may show that a prior rationale changes rule-grounded evidence updating in these synthetic conversations and that a tested workflow changes that effect. It cannot establish whether a real complaint process is fair, accessible, trusted, lawful, or effective. Those questions require affected communities, domain professionals, accountable organizations, and real institutional procedures.
