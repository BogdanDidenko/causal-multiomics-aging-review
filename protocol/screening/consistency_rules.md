# Deterministic Consistency Rules

The model classifies atomic criteria. Python applies only logical relations
between those criteria; it does not infer eligibility from keywords.

## Title/abstract

1. The model independently classifies four aging-role indicators. Python
   derives `aging_role` with this fixed precedence:

| Condition | Derived aging role |
|---|---|
| `aging_process_relevance=no` | `age_context_only` |
| `aging_process_relevance=unclear` | `unclear` |
| intervention target analyzed `yes` | `aging_intervention_target` |
| longevity/healthspan analyzed `yes` | `longevity_or_healthspan` |
| aging measure/trajectory analyzed `yes` | `aging_outcome_or_trajectory` |
| aging mechanism analyzed `yes` | `aging_mechanism` |
| no indicator is `yes` | `unclear` |

   When relevance is `no`, all four indicators are normalized to `no`.

2. When `aging_process_relevance=no`, the review-specific causal fields become:
   `causal_claim_present=no`,
   `identification_status=no_relevant_design`, `design_families=[]`, and
   `design_role=mentioned_only`. A design about an unrelated disease cannot be
   relevant to the aging review.
3. Report-level `design_role` is derived from `identification_status`:

| Identification status | Derived design role |
|---|---|
| `identified` | `primary_identification` |
| `hypothesis_only` | `hypothesis_generation` |
| `association_only` | `mentioned_only` |
| `no_relevant_design` | `mentioned_only` |
| `unclear` | `unclear` |

4. The model independently classifies three observable multi-omics facts:
   `same_sample_or_participants`, `distinct_molecular_datasets_linked`, and
   `cross_layer_operation_reported`. Python derives `integration_mode` with
   this fixed precedence:

| Condition | Derived integration mode |
|---|---|
| `multiomics_status=unclear` | `unclear` |
| `multiomics_status=no` and all layers contextual or report nonempirical | `external_context_only` |
| `multiomics_status=no` otherwise | `single_layer_only` |
| `distinct_molecular_datasets_linked=yes` | `cross_dataset_integrated` |
| same sample `yes` and cross-layer operation `yes` | `same_study_joint_integration` |
| same sample `yes` and cross-layer operation `no` | `same_study_parallel_measurement` |
| any other multi-omics combination | `unclear` |

This rule does not infer whether a study is multi-omics. It only converts
model-classified provenance facts into a normalized integration label.

The provider's unmodified JSON is retained in
`raw_provider_responses.jsonl`. Normalized criterion output and the names of
applied rules are stored in `screening_results.jsonl`.

## Full text

Python derives evidence level and final study label from eligibility,
identification, estimand completeness, assessable assumptions, and aligned
validation fields. The model never selects its own evidence level or final
label.
