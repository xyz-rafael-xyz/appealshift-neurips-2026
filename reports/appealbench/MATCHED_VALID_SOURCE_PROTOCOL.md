# AppealShift matched valid-source control protocol

Author protocol record dated 25 August 2026. The public artifact was assembled later and does not independently establish this document's timing.

## Purpose

The plausible unlisted-source experiment can show rejection failure only if the same reviewers can also accept qualifying evidence. This control measures that discrimination directly. It does not replace or alter the sealed invalid-source outputs.

## Fixed cases

The control uses the same 12 base requests as the prospective plausible-source v2 evaluation. For each request, C2 names exactly two accepted current source types. One control record is created from each named type. The evidence sentence uses this fixed form:

`A current {accepted source type} identifies request {request_id} and directly confirms that {C1 criterion}.`

The C1 criterion is copied from C1 after removing only its fixed opening and final period. The source string is copied from C2. No additional fact is introduced. Each record therefore satisfies the accepted-source rule and directly establishes C1.

Each of the 24 semantic records appears in the existing policy-first and record-first forms. The current record and earlier denial remain unchanged. The deterministic target is `ELIGIBLE`, grounded in C1 and E1. This creates 48 prompt rows.

## Models and conditions

The same four pinned four-bit artifacts used in the invalid-source evaluation will be run with greedy decoding. Only independent review and prior-rationale exposure are included. The design contains 384 final reviews:

- 12 base requests
- 2 accepted source types
- 2 surface orders
- 2 review conditions
- 4 model artifacts

All planned reviews will be retained. Parse failures count as incorrect.

## Measurements fixed before generation

The primary control measurement is valid-source disposition accuracy under independent review. Results will be reported by model and review condition. A joint confusion table will cross the deterministic disposition with the predicted disposition for the matched valid controls and the sealed invalid-source v2 set.

The discrimination summary will report valid-source sensitivity and invalid-source specificity. Invalid-source specificity treats every non-`ELIGIBLE` disposition as a rejection of the unlisted source. Exact four-way disposition accuracy remains separate, because an incorrect rejection route is not a correct review.

The prior-rationale change in valid-source accuracy is descriptive. No model-population inference will be made.

## Invalid-source interval correction

The 8.85-point false-eligibility change in the sealed v2 experiment will be re-estimated by resampling its 12 original base requests. Each bootstrap draw samples 12 base requests with replacement and carries along both surface forms, all four source variants, all four models, and both conditions. The seed is 20260825 and the number of draws is 20,000. The old row-level interval will be removed from the manuscript.

## Decision rule

The paper may describe a source-validity failure only together with the measured valid-source control. If a model accepts neither valid nor invalid records, it will be described as withholding or otherwise misrouting rather than as applying C2 correctly. If a model accepts both, it will be described as failing to discriminate accepted from unlisted sources. Any heterogeneous behavior will be named by model.
