# AppealShift plausible-source evaluation protocol v2

Author protocol record dated 24 August 2026. It states that the design was fixed before generating any v2 model output. The public artifact was assembled later and does not independently establish that sequence.

## Motivation and provenance

The first plausible-source slice used 12 semantic cases and was inspected as an exploratory analysis. It remains exploratory. The v2 evaluation uses the other 12 invalid-evidence cases from the frozen evaluation bank. None of those 12 cases has appeared in the first plausible-source slice. Their original simple invalid-record outputs exist in the main experiment, but no output has been generated for the four v2 source variants defined below.

## Fixed design

Each of the 12 source cases receives four current-looking but unlisted evidence records. The variants are a coordination digest, a forwarded screenshot, an unsigned portal export, and a staff chat summary. Each record repeats the eligibility fact while explicitly failing the accepted-source rule. Every case appears in both frozen surface orders. This produces 48 semantic cases and 96 prompt variants.

The same four pinned four-bit model artifacts are evaluated under independent review and prior-rationale exposure. Decoding is greedy. The design therefore contains 768 final reviews. Existing prompts, parsers, and deterministic disposition and grounding scorers are unchanged.

## Primary measurements

The primary measurement is exact disposition accuracy under independent review, pooled across the four fixed artifacts and reported separately for each artifact. The accompanying safety measurement is false eligibility on the same reviews. Both measurements will also be printed for each source variant and surface order.

The prior-rationale minus independent-review paired change is secondary. Fully grounded correctness and order disagreement are descriptive. No population-of-models claim will be made. Any interval will cluster on the 48 semantic cases and will describe only this fixed model pool.

## Decision rule

The v2 result supports the narrow evidence-validity finding only if independent-review accuracy remains below 25 percent in the pooled fixed-artifact summary and no model exceeds 50 percent. Otherwise the paper will report the heterogeneous result and will not claim broad failure on plausible unlisted sources. Rationale exposure will not be called beneficial unless it improves exact disposition accuracy without increasing false eligibility.

## Stopping and reporting

All 768 planned reviews will be retained. There is no outcome-based stopping. Parse failures count as incorrect and remain visible. The manuscript will distinguish the inspected v1 exploratory slice from the larger v2 evaluation supplied in the artifact.
