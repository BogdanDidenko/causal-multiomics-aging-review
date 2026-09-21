# Causal Multi-omics Aging Content Model v1.0.0

## Foundation

CMACM Foundation is the canonical, many-to-many content layer. It is not a
table and has no global `analysis_count`.

| Entity | Fully specified meaning |
|---|---|
| `ReportVersion` | A citable preprint, publisher article, correction, supplement, or revision. |
| `Study` | A bounded empirical investigation, cohort, experiment, or dataset application. |
| `CausalWorkflow` | A coherent causal procedure within one study. |
| `CausalLink` | A directed exposure/intervention-to-outcome claim in a stated system. |
| `Contrast` | The exact comparison, estimand, arm, dose, direction, time point, estimator, or subgroup supporting a link. |
| `Validation` | A replication, rescue, orthogonal assay, sensitivity analysis, negative control, or challenge with a target and result. |
| `SourceEvidence` | A report-local quotation, table, figure, supplement, or method statement. |
| `ExtractionAssertion` | A model or human interpretation, with lifecycle status and source evidence. |

## Relations

`describes(ReportVersion, Study)`

`contains(Study, CausalWorkflow)`

`asserts(CausalWorkflow, CausalLink)`

`evaluated_by(CausalLink, Contrast)`

`targets(Validation, CausalWorkflow|CausalLink|Contrast)`

`supported_by(any entity or relation, SourceEvidence)`

`extracted_from(ExtractionAssertion, SourceEvidence)`

`adjudicates(ExtractionAssertion, Foundation entity or relation)`

## Individuation Rule

Create a new `CausalWorkflow` only when the study context, causal procedure, or
identity-defining exposure/instrument changes. Create a new `CausalLink` only
when exposure/instrument, outcome construct, direction, or biological system
changes. Use `Contrast` axes for treatment level, comparator, estimator,
timepoint, dose, subgroup, and adjustment specification. Use `Validation` for
rescue, replication, orthogonal assay, sensitivity analysis, negative control,
or challenge.

## Link Conditions

A link may be assigned `effect_identification_design` only when it has a
reported exposure/instrument, outcome, direction, biological system, causal
procedure, and at least one exact source-evidence locator. A link with a formal
directed method but insufficient identification receives
`formal_directed_hypothesis`. A report lacking either route has no causal link
in the causal-link linearization.

## Postcoordination Axes

| Entity | Required axes | Repeatable axes |
|---|---|---|
| `CausalWorkflow` | `causal_basis`, `design_family`, `biological_system`, `aging_phenomenon`, `integration_operator` | `omics_layer`, `layer_role` |
| `CausalLink` | `exposure_or_intervention`, `outcome_construct`, `direction`, `assertion_polarity` | `assumption`, `diagnostic` |
| `Contrast` | `comparator` | `arm`, `dose`, `timepoint`, `subgroup`, `estimator`, `adjustment` |
| `Validation` | `validation_type`, `result`, `independence` | `transfer_context` |
| `SourceEvidence` | `report_version_id`, `source_locator`, `verbatim_quote` | `supports_field` |
| `ExtractionAssertion` | `extractor`, `activity`, `status` | `known_inconsistency` |

## Linearizations

The Foundation generates purpose-specific, mutually exclusive views. Each view
declares its counting unit.

1. `prisma_report_view`: report versions and retrieval/eligibility disposition.
2. `evidence_base_view`: canonical studies, systems, aging constructs, and workflow families.
3. `causal_leverage_view`: `CausalWorkflow` counted by design family.
4. `multiomics_contribution_view`: `CausalWorkflow` counted by integration operator and layer role.
5. `aging_outcome_view`: `CausalLink` counted by aging phenomenon stratum.
6. `strength_transport_view`: `Validation` entities, each mapped to its target link and assertion polarity.
7. `audit_view`: extraction assertions and source evidence.

No linearization may relabel a report count as a study, workflow, link,
contrast, validation, or evidence count.
