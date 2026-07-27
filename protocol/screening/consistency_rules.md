# Deterministic Consistency Rules

The model classifies atomic criteria. Python applies only logical relations
between those criteria; it does not infer eligibility from keywords.

## Title/abstract

1. Report type is localized to the decisive IC1 contract:
   `empirical_primary`, `nonempirical`, or `unclear`. Review, protocol,
   method-only, and resource subtypes are deferred because they share the same
   title/abstract route and exclusion code.
2. The title/abstract model directly classifies a localized aging role using a
   closed precedence table: applied aging intervention, organismal
   longevity/healthspan, other aging measure or process, age context only, or
   unclear. Mechanism versus outcome/trajectory is deferred to full text
   because it has no title/abstract routing consequence. Python does not infer
   the aging construct from keywords.
3. When `aging_process_relevance=no`, the adjudicated review-specific causal
   fields become:
   `causal_claim_present=no`,
   `identification_status=noncausal`,
   `primary_design_family=none`, `design_families=[]`, and
   `design_role=mentioned_only`. The independent causal reviewer can still
   describe a report-level design before review-specific adjudication.
4. Title/abstract `causal_claim_present`, `design_role`, and the compatibility
   `design_families` list are derived from `identification_status` and the one
   model-selected primary design family:

| Identification status | Derived design role |
|---|---|
| `identified` | `primary_identification` |
| `hypothesis_only` | `hypothesis_generation` |
| `noncausal` | `mentioned_only` |
| `association_only` | `mentioned_only` |
| `no_relevant_design` | `mentioned_only` |
| `unclear` | `unclear` |

5. Python checks the model-extracted molecular-layer list. Two or more distinct
   non-contextual normalized layers imply `multiomics_status=yes`; a claimed
   `yes` with fewer than two supported layers becomes `unclear`.
6. PRISMA criteria are ordered. After a nonempirical report type or
   `aging_process_relevance=no`, title/abstract multi-omics becomes
   `not_assessed` and its layer list is cleared. Detailed same-sample
   provenance, cross-layer operations, integration mode, and secondary design
   families are assessed only at full text.

The title/abstract exclusion mapping follows the same criterion order:
`EC1=nonempirical`, `EC2=non-biological/health`, `EC3=non-aging`,
`EC4=non-multi-omics`, and `EC5=noncausal`.

The provider's unmodified JSON is retained in
`raw_provider_responses.jsonl`. Normalized criterion output and the names of
applied rules are stored in `screening_results.jsonl`.

## Full text

Python derives evidence level and final study label from eligibility,
identification, estimand completeness, assessable assumptions, and aligned
validation fields. The model never selects its own evidence level or final
label.
