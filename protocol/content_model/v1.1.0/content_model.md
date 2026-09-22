# Causal Multi-omics Aging Content Model v1.1.0

## Foundation

CMACM Foundation is the canonical, many-to-many content layer. It is not a
table and has no global `analysis_count`.

| Entity | Fully specified meaning |
|---|---|
| `ReportVersion` | A citable preprint, publisher article, correction, supplement, or revision. |
| `Study` | A bounded empirical investigation, cohort, experiment, or dataset application. |
| `CausalWorkflow` | A derived identity defined by `Study + causal procedure class + analysis population/dataset context`. |
| `CausalLink` | A derived identity defined by `Workflow + exposure/intervention family + normalized outcome domain + direction + biological system`. |
| `ResultMeasurement` | A non-countable endpoint, assay, effect estimate or statistic under one link and contrast cluster. |
| `Validation` | A replication, rescue, orthogonal assay, sensitivity analysis, negative control, or challenge with a target and result. |
| `SourceEvidence` | A report-local quotation, table, figure, supplement, or method statement. |
| `ExtractionAssertion` | A model or human interpretation, with lifecycle status and source evidence. |

## Relations

`describes(ReportVersion, Study)`

`contains(Study, CausalWorkflow)`

`asserts(CausalWorkflow, CausalLink)`

`targets(Validation, CausalWorkflow|CausalLink|Contrast)`

`supported_by(any entity or relation, SourceEvidence)`

`extracted_from(ExtractionAssertion, SourceEvidence)`

`adjudicates(ExtractionAssertion, Foundation entity or relation)`

## Individuation Rule

Create a new `CausalWorkflow` only when study, causal procedure class, or
analysis population/dataset context changes. Exposure, target, instrument, arm,
dose, endpoint, direction and estimator do not create a workflow.

Create a new `CausalLink` only when derived workflow, exposure/intervention
family, normalized outcome domain, direction, or biological system changes.
Individual biomarkers, phenotypes, assays and quantitative results are
`ResultMeasurement` records, never links. A `Contrast` is an axis cluster with
comparator, arm, dose, timepoint, estimator and adjustment values.

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
| `CausalWorkflow` | `causal_procedure_class`, `analysis_population_dataset_context`, `biological_system`, `aging_phenomenon`, `integration_operator` | `omics_layer`, `layer_role` |
| `CausalLink` | `exposure_intervention_family`, `normalized_outcome_domain`, `direction`, `assertion_polarity` | `assumption`, `diagnostic` |
| `ResultMeasurement` | `endpoint_specification`, `assay_or_instrument` | `effect_estimate`, `interval`, `statistic`, `unit` |
| `Contrast` axis cluster | `comparator` | `arm`, `dose`, `timepoint`, `subgroup`, `estimator`, `adjustment` |
| `Validation` | `validation_type`, `result`, `independence` | `transfer_context` |
| `SourceEvidence` | `report_version_id`, `source_locator`, `verbatim_quote` | `supports_field` |
| `ExtractionAssertion` | `extractor`, `activity`, `status` | `known_inconsistency` |

## Linearizations

The Foundation generates purpose-specific, mutually exclusive views. Each view
declares its counting unit.

1. `prisma_report_view`: every `ReportVersion` in scope.
2. `evidence_base_view`: every `Study` in scope.
3. `causal_leverage_view`: every `CausalWorkflow` in scope, counted by design family.
4. `multiomics_contribution_view`: only `CausalWorkflow` entities with one or more molecular omics layers.
5. `aging_outcome_view`: only `CausalLink` entities whose normalized outcome domain has an analytic aging role.
6. `strength_transport_view`: every `Validation` entity, each mapped to its target link and assertion polarity.
7. `audit_view`: every `ExtractionAssertion` for the output record.

No linearization may relabel a report count as a study, workflow, link,
contrast, validation, or evidence count.
