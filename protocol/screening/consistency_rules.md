# Deterministic Consistency Rules

The model classifies semantic criteria. Python applies only ordered logical
relations between those criteria; it does not infer eligibility from keywords.

## Title/abstract

The active categorical contract is:

- `report_type`: `empirical_primary | nonempirical | unclear`;
- `bio_health_scope`: `yes | no | unclear | not_assessed`;
- `aging_process_relevance`: `yes | no | unclear | not_assessed`;
- `multiomics_status`: `yes | no | unclear | not_assessed`;
- `identification_status`: `causal_candidate | noncausal | unclear`.

Python applies these rules in order:

1. If report type is not `empirical_primary`, biological scope, aging
   relevance, and multi-omics become `not_assessed`.
2. Otherwise, if biological scope is not `yes`, aging relevance and
   multi-omics become `not_assessed`.
3. Otherwise, if aging relevance is not `yes`, multi-omics becomes
   `not_assessed`.
4. A nonempirical report or explicit `aging_process_relevance=no` makes the
   review-specific causal status `noncausal`. An `unclear` aging value does not
   suppress independent causal-candidate assessment.
5. Exact title-stage omics-layer inventory is always cleared and deferred to
   full text.
6. Clear Round-A exclusions route directly. Any unresolved criterion routes to
   adjudication; an adjudicated `unclear` record proceeds to full text.

The title/abstract exclusion mapping follows the same criterion order:
`EC1=nonempirical`, `EC2=non-biological/health`, `EC3=non-aging`,
`EC4=non-multi-omics`, and `EC5=noncausal`.

The provider's unmodified JSON is stored in
`raw_provider_responses.jsonl`. Normalized criteria and each applied rule name
are stored in `screening_results.jsonl`.

## Full text

Python derives evidence level and final study label from eligibility,
identification, estimand completeness, assessable assumptions, and aligned
validation fields. The model never selects its own evidence level or final
label.

Full-text evidence levels remain:

- Level 0: context-only or no multi-omics;
- Level 1: association or prediction without causal identification;
- Level 2: causal hypothesis, directed model, or mediation without sufficient
  identification;
- Level 3: assessable causal effect with a defined contrast or estimand and
  inspectable assumptions;
- Level 4: Level 3 plus aligned independent replication or validation of the
  same causal link.
