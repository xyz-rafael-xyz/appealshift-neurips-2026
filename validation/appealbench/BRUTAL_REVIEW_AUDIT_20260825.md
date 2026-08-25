# AppealShift brutal-review audit

The 12-cluster false-eligibility resampler was rerun from the stored source-comparison records and reproduced `experiments/appealbench/source_discrimination_analysis.json` byte for byte. It computes 32 paired condition effects inside each base request, averages those effects within the base, and resamples the resulting 12 means. The base means are 0.03125 to 0.125 and all are positive. The 20,000-draw interval remains 0.0729167 to 0.104167 around an effect of 0.0885417.

The fixed five-case Phi audit is recorded in `validation/appealbench/phi_grounding_five_case_audit.json`. All five outputs have the correct `INELIGIBLE` disposition and cite the wrong policy clause. One also omits E1. The observed failures are therefore substantive attribution errors in this sample, not alternative JSON formatting.

The manuscript now states that `INELIGIBLE` is the exact target only because fictional clause C2 specifies that mapping. A service designer could instead request an accepted record and map the case to `NEED_INFORMATION`. AppealShift measures adherence to the printed synthetic policy and does not claim that its mapping is the humane optimum.

The practitioner request remains a draft. No external review has occurred, and the paper claims none.
