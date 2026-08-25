# AppealShift novelty audit

## Proposed contribution

AppealShift will test whether exposure to an earlier denial rationale changes how instruction-tuned language models apply new evidence during a fictional humanitarian-service review. It will also test two simple review workflows that may reduce any observed inertia. The study uses explicit fictional policies, exact disposition labels, paired prompts, and deterministic scoring.

The intended contribution is a controlled behavioral audit. It is not a new theory of contestability, a legal appeal generator, a production adjudication system, or a claim about real humanitarian institutions.

## Closest work and the remaining gap

| Prior work | What already exists | Boundary retained for AppealShift |
|---|---|---|
| [Explainable AI Isn't Enough](https://arxiv.org/abs/2605.16041) | An operational definition of contestability and three evidence types that can justify overturning a decision | Do not claim a new definition or evidence taxonomy. Test update behavior under controlled appeal evidence. |
| [Conceptualising Contestability](https://arxiv.org/abs/2103.01774) | A multi-perspective account of contesting algorithmic decisions | Treat contestability as a sociotechnical process and avoid reducing it to model accuracy. |
| [Humans in the Contestability Loop](https://doi.org/10.1145/3805689.3812271) | Participatory design for social counselors contesting welfare-fraud decisions, with conversational explanations and human intervention | Do not claim a new conversational interface. Evaluate one model behavior that such interfaces could expose. |
| [Operationalizing AI contestability](https://doi.org/10.1007/s44163-026-01381-2) | Cross-domain assessment of which contestability components are technically feasible | Do not equate technical feasibility with effective contestability. |
| [AppealCase](https://arxiv.org/abs/2505.16514) | 10,000 matched civil-case appeal pairs with reversal and new-information tasks | Avoid legal cases and judgment prediction. Use fictional humanitarian policies and causal prompt pairing. |
| [AppellateGen](https://arxiv.org/abs/2601.01331) | 7,351 legal case pairs and appellate judgment generation over earlier verdicts and evidentiary updates | Do not claim the first evidence-updating appeal benchmark. Study rationale exposure and concise service-review dispositions. |
| [Reviewing the Reviewer](https://arxiv.org/abs/2603.19267) | A production e-commerce appeal workflow with evidence, actions, requests for information, and graph retrieval | Do not claim that structured evidence or request-for-information outcomes are new. Evaluate small, reproducible prompt workflows without proprietary records. |
| [Pro-Judice](https://doi.org/10.3233/FAIA251616) | A benchmark of procedural-fairness perceptions in judicial settings | Avoid broad procedural-fairness claims and judicial simulation. |
| [LLMs on Trial](https://arxiv.org/abs/2507.10852) | A 177,100-instance benchmark of substantive and procedural judicial fairness | Do not claim the first procedural audit of LLM decisions. |
| [Large Language Models Cannot Self-Correct Reasoning Yet](https://openreview.net/forum?id=IkmD3fKBPQ) | Evidence that unsupported self-correction can fail and can damage correct answers | Compare review workflows on externally supplied policy and evidence rather than relying on introspection. |
| [Arguments that Alter Minds](https://aclanthology.org/2026.acl-long.599/) | Controlled evidence that pro and con rationales shift human and LLM plausibility ratings on commonsense questions | Do not claim the first causal test of rationale exposure. Test final policy dispositions in a service-review process where the earlier rationale should carry no evidentiary weight. |
| [Prior Beliefs Prejudice LLM-as-Judge](https://aclanthology.org/2026.findings-acl.2087/) | A 27,756-item persuasion dataset showing that model beliefs can distort ratings of rhetorical quality | Separate AppealShift from belief alignment and persuasion quality. Its manipulated text is an earlier case rationale, and its outcome is exact compliance with stated policy. |
| [Anchoring Depends on Confidence and Post-Training in Language Models](https://aclanthology.org/2026.acl-short.16/) | Numerical anchoring effects across model variants and confidence levels | Do not claim the first LLM anchoring study. Treat any prior-rationale effect as procedural carryover in a categorical evidence-review task. |
| [Prior Audit-Repair Context Shifts LLM Verifier Thresholds Toward Leniency](https://arxiv.org/abs/2608.16003) | A controlled context experiment where a completed audit and repair episode about another item shifts false-alarm thresholds on a byte-identical verification task | This is the closest recent context-effect design. AppealShift shows or hides a case-specific earlier denial rationale while holding the current policy and appeal evidence fixed, then scores categorical review dispositions across four evidence states. |

## Humanitarian grounding

The [Core Humanitarian Standard](https://www.corehumanitarianstandard.org/the-standard) asks organizations to support crisis-affected people in ways that respect rights and dignity, address power imbalances, and allow communities to hold organizations to account. ICRC analysis of [AI in humanitarian action](https://international-review.icrc.org/articles/harnessing-the-potential-of-artificial-intelligence-for-humanitarian-action-919) says people should be able to challenge adverse automated or AI-supported decisions and points to grievance mechanisms as routes to remedy. The ICRC's [human-centred position](https://international-review.icrc.org/articles/ai-and-machine-learning-in-armed-conflict-a-human-centred-approach-913) also stresses accountability, human involvement, realistic capability assessments, and do-no-harm practice.

These sources motivate the study. They do not validate the synthetic policies or make the benchmark an institutional complaint mechanism.

## Search conclusion

Searches through 22 August 2026 found legal appeal datasets, judicial fairness benchmarks, human-centered contestability interfaces, implementation frameworks, self-correction studies, rationale-persuasion experiments, numerical anchoring studies, a production e-commerce appeal system, and a recent audit-repair context experiment. No located primary study jointly used all four elements below.

- Fictional humanitarian-service reviews tied directly to crisis-response accountability
- A matched causal manipulation that shows or hides the earlier denial rationale
- Valid, invalid, incomplete, and conflicting appeal evidence under explicit symbolic policies
- A comparison of direct review with evidence-checklist and independent-commitment workflows

This is a narrow search-supported gap, not proof that no unpublished or unindexed work exists. The submission should say that prior work leaves this combination untested. It should not say first, unprecedented, or unique.

## Claims allowed before results

- We introduce a synthetic paired audit for humanitarian-service appeal conversations.
- The design isolates exposure to an earlier denial rationale while holding the policy, case facts, and new evidence fixed.
- Exact rules support deterministic disposition and grounding scores.
- The benchmark tests conversational behavior and does not instantiate a real remedy.

## Claims forbidden

- AppealShift guarantees fair humanitarian decisions.
- AppealShift implements a right to appeal.
- The tested models represent all language models.
- Synthetic correctness predicts institutional justice or user experience.
- The benchmark is the first work on contestability, appeals, new evidence, or procedural fairness.
- The benchmark is the first causal study of rationale exposure or anchoring in language models.
- Any prompt workflow should be deployed in crisis response without participatory design and accountable human authority.

## Claim-level update on 23 August 2026

[Sycophants in the Courtroom](https://aclanthology.org/2026.acl-long.497/) establishes model susceptibility to authoritative false information and superficial legal formatting. [From Fact to Judgment](https://aclanthology.org/2026.iwsds-1.21/) establishes changes from minimal conversational framing and rebuttal. AppealShift makes no general claim about authority or dialogue effects. It shows or hides an earlier denial rationale for the same case, holds current evidence and policy fixed, and measures how errors move across four evidence states. The paper and artifact now use this matched evidence-state boundary.
