# AppealShift dual-convention scoring protocol

Status: fixed on 2026-08-27 for the reported post-audit sensitivity analysis. A smoke run exposed the condition denominators before this protocol entered Git history, so the analysis is not described as preregistered.

This deterministic post-audit analysis uses existing frozen outputs. It makes no model calls.

## Question

How much does exact-disposition performance depend on whether an invalid appeal should end in `INELIGIBLE`, as printed in the study, or `NEED_INFORMATION`?

## Frozen scoring

- Invalid-source outputs: the complete four-model `adversarial_v2` runs
- Matched valid-source outputs: the complete four-model `matched_valid_controls` runs
- Printed convention: invalid target `INELIGIBLE`, valid target `ELIGIBLE`
- Alternative convention: invalid target `NEED_INFORMATION`, valid target `ELIGIBLE`
- Conditions: independent and prior rationale
- Metric: exact disposition
- Balanced score: arithmetic mean of valid-source and invalid-source exact accuracy

The report gives valid and invalid denominators, exact accuracy under each convention, and the balanced score for every model and condition. Source discrimination remains a separate binary endpoint and is not rescored.
