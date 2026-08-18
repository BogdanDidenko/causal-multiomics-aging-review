# Claim-level causal identification codebook v0.2.0

## Status and purpose

This is an instrument-development revision for causal evidence extraction from
the 101 full-text-eligible reports. It incorporates the primary-analyst pilot
and an independent read-only Claude Opus 5 audit. It does not change
eligibility, PRISMA counts, or the completed screening decisions.

The codebook separates factual extraction from review judgment. Its purpose is
to prevent a named method, an author causal verb, a fine-mapping rank, or a
model-generated graph label from being treated as sufficient evidence of
causal identification. Candidate evidence levels and Level 4 qualification are
derived by code and are not annotated by a reviewer.

## Unit of annotation

The unit is one normalized causal claim:

`one exposure operation -> one outcome -> one comparator/contrast -> one system and time horizon`

A report may contribute several claims. Split claims when any of the following
changes:

- the intervention or exposure operation;
- the outcome or endpoint depth;
- the population, organism, tissue, or cell system;
- the comparator or time horizon;
- the identification strategy;
- the result direction or null/conflicting status.

Do not classify a whole report by its strongest experiment. Omics discovery,
target perturbation, post-intervention molecular response, mediation, and
external validation are separate claims when they concern different links.

Split endpoint families unless the source reports a prespecified composite or
one assay-platform contrast under one multiplicity correction. Split strata
when system, population, dose range, or result direction changes. Use
`conflicting_within_report` only when evidence for one normalized link is
internally contradictory; different operations or strata remain separate
claims.

Two extraction modes are allowed and must be declared before annotation:

- `exhaustive_report`: enumerate every claim meeting the review's causal-claim
  definition in the report;
- `boundary_case_pilot`: annotate prespecified claims selected to test a
  codebook boundary. Omitted claims are not segmentation disagreements, but a
  selected record must still obey all split rules.

Production extraction and inter-rater validation use `exhaustive_report`.

## Core fields

### 1. `author_claim_type`

What the authors claim, independent of whether the review accepts it:

| Value | Definition |
| --- | --- |
| `causal_effect` | The report claims that changing or varying an exposure changes an outcome. |
| `mechanism_or_mediation` | The report claims necessity, sufficiency, rescue, pathway dependence, or mediation. |
| `directed_hypothesis` | A formal method proposes direction or a causal structure without an identified effect. |
| `association_prediction_or_prioritization` | Association, prediction, enrichment, docking, colocalization-only, or candidate ranking. |
| `unclear` | The claim cannot be determined from the available text. |

Author wording is not the reviewer judgment. A paper may claim causality while
the reviewer assigns `no_identification`.

### 2. `design_or_method`

Record one primary design or method for the annotated claim:

- `randomized_intervention`;
- `controlled_nonrandomized_intervention`;
- `quasi_experiment`;
- `targeted_genetic_perturbation`;
- `targeted_pharmacologic_perturbation`;
- `biological_transfer`;
- `genetic_instrument`;
- `mediation_analysis`;
- `temporal_model`;
- `dag_scm`;
- `sem`;
- `bayesian_network`;
- `causal_discovery_algorithm`;
- `invariance_or_environment_based_model`;
- `predictive_or_associational_model`;
- `computational_prioritization`;
- `other_formal_design`;
- `none`;
- `unclear`.

Supporting methods are recorded separately. Method names do not determine the
evidence level.

### 3. `variation_sources`

Record what creates each contrast used for the claim. Each item contains a
`link_role` and `source`. A two-node claim normally has one item. Mediation and
other multi-node claims record every link needed for the claimed effect rather
than forcing the entire claim into one source.

`link_role` is one of:

- `exposure_to_outcome`;
- `exposure_to_mediator`;
- `mediator_to_outcome`;
- `intervention_to_outcome`;
- `directed_pair`;
- `other`.

| Value | Typical examples |
| --- | --- |
| `randomized_assignment` | Random allocation to intervention or control. |
| `investigator_assigned_exposure` | Controlled treatment without documented randomization. |
| `engineered_or_targeted_perturbation` | Knockout, knockdown, overexpression, CRISPR, or target-directed inhibitor. |
| `transferred_biological_material` | FMT, parabiosis, plasma, cells, or other transferred material. |
| `inherited_genetic_variation` | Germline genotype generates the contrast, regardless of instrument validity. |
| `quasi_exogenous_rule_or_event` | Threshold, policy, natural experiment, or other plausibly exogenous assignment. |
| `within_unit_temporal_variation` | Repeated observations or lagged change without another exogenous source. |
| `observational_covariation` | Unassigned between-person, between-tissue, or between-feature variation. |
| `none` | Prediction or prioritization with no identifying contrast. |
| `unclear` | Source cannot be established from the available text. |

This field describes provenance of a link-specific contrast, not its validity.
MR, TWAS with genotype-derived expression weights, and summary-data MR use
inherited variation even when relevance, independence, or exclusion
restriction is not adequately addressed. Those limitations belong in
assumption judgments and the reviewer assessment.

For mediation, do not claim that one link alone "carries" the indirect effect.
Record exposure-to-mediator and mediator-to-outcome sources separately. For a
directed pair, record variation in that measured pair rather than an unrelated
environmental grouping variable.

### 4. `assignment_mechanism`

Record how units received the exposure or intervention, orthogonally to what
the exposure material was:

- `randomized`;
- `investigator_assigned_nonrandom`;
- `quasi_exogenous_rule_or_event`;
- `unassigned_observational`;
- `inherited`;
- `none`;
- `unclear`.

Thus randomized parabiosis is `transferred_biological_material` plus
`randomized`, whereas nonrandom FMT is `transferred_biological_material` plus
`investigator_assigned_nonrandom`.

### 5. `reviewer_identification_assessment`

| Value | Definition |
| --- | --- |
| `effect_assessable` | A defined contrast or estimand and an inspectable identification strategy exist for the stated system. This does not imply low risk of bias or transportability. |
| `effect_claim_not_assessable` | Authors make an effect claim, but the contrast, estimand, assignment, temporal order, or key assumptions are not sufficiently specified or are fatally incompatible with that claim. |
| `formal_hypothesis_only` | A formal directed, mediation, temporal, structural, or discovery method supports a testable hypothesis but not an assessable effect. |
| `no_identification` | The evidence is associational, predictive, descriptive, or prioritizing only. |
| `unclear` | The supplied full text is insufficient for classification. |

`effect_assessable` means that the causal contrast can be appraised. It is not a
quality label. Design-specific limitations and violated assumptions remain
visible and may make the estimate weak or biased.

A null tested contrast may still be `causal_effect` and `effect_assessable`.
Result direction is recorded only in `result_status`.

## Required claim fields

Each claim record contains:

- report DOI, stable `claim_id`, and declared `extraction_mode`;
- source-adequacy status and available document sections;
- normalized claim statement;
- exact exposure/intervention and `exposure_operation`;
- comparator;
- outcome;
- population/model and biological system;
- time horizon;
- `author_claim_type`;
- primary and supporting `design_or_method` values;
- link-specific `variation_sources` and an orthogonal `assignment_mechanism`;
- method output type;
- contrast/estimand statement and completeness;
- design-specific assumptions and diagnostics;
- `reviewer_identification_assessment`;
- result status;
- controlled-vocabulary omics roles;
- validation records;
- status indicating whether the report proposes validation;
- field-level evidence-anchor references for every decision-driving field;
- evidence anchors from the deterministic full text.

`candidate_level`, `formal_basis_present`, and `qualifies_for_level4` are not
reviewer fields. Python derives them from the atomic record.

## Method output types

Use the most specific output represented by the claim:

- `total_effect`;
- `direct_or_controlled_effect`;
- `indirect_effect`;
- `necessity`;
- `sufficiency`;
- `rescue`;
- `effect_modification_or_epistasis`;
- `post_intervention_molecular_response`;
- `genetically_proxied_effect`;
- `temporal_ordering`;
- `directed_edge_or_structure`;
- `prediction`;
- `candidate_prioritization`;
- `other`;
- `unclear`.

Necessity, sufficiency, rescue, and effect modification must not be collapsed.
For loss of function, use `necessity` only when the claim states that the target
is required for the outcome. For gain of function or transfer, use
`sufficiency` only when the claim states that the operation can induce the
outcome. Use `total_effect` for a condition contrast without a necessity or
sufficiency assertion. Use `effect_modification_or_epistasis` for a
genotype-by-treatment or perturbation-by-treatment comparison and record
whether an interaction estimand was tested.

Pharmacologic inhibition, transcript knockdown, protein depletion, germline
knockout, and overexpression are different exposure operations even when they
share a gene symbol.

## Contrast components

Record six atomic `yes | no | unclear | not_applicable` fields:

1. `operation_specified`;
2. `comparator_specified`;
3. `outcome_specified`;
4. `population_and_system_specified`;
5. `time_horizon_specified`;
6. `effect_measure_or_logical_contrast_specified`.

Python derives `contrast_complete=yes` only when every applicable component is
`yes`. Completeness describes specification, not validity. Confounding,
misallocation, temporal incompatibility, or failed assumptions belong in the
assumption module and reviewer assessment; they do not change a specified
component to `no`.

## Design-specific assumption modules

Record each assumption as `addressed`, `not_reported`, `violated`,
`not_applicable`, or `unclear`, with an evidence anchor.

`addressed` means that the report explicitly provides a design feature,
analysis, diagnostic, or stated argument bearing on the assumption. It does not
mean the assumption holds or that handling is adequate. `violated` is reserved
for a source-demonstrated factual incompatibility. An author's disclaimer that
causality cannot be established is not itself an assumption violation.

Assumption domains use the closed vocabulary in the JSON Schema. Python maps
the primary design to required domains and requires every domain to be present;
`not_reported` is an explicit result and must not be represented by omission.
Supporting designs add their own required domains when they contribute to the
annotated claim. `addressed`, `violated`, and `unclear` require an evidence
anchor. `not_reported` requires a search note naming the inspected sections,
because absence cannot be supported by a fabricated quotation.

### Assigned intervention

- allocation mechanism and concealment where applicable;
- comparator integrity;
- adherence and contamination;
- attrition and analysis population;
- baseline balance;
- correct between-group or assigned-contrast analysis;
- outcome timing and multiplicity.

Randomization of treatment identifies only treatment effects analyzed through
the randomized contrast. It does not identify a molecular mediator, a
within-arm dose trend, or a baseline predictor of response.

### Targeted perturbation

- exact manipulated operation and target;
- matched control;
- intervention specificity or off-target evidence;
- timing relative to outcome;
- replication;
- necessity, sufficiency, or rescue logic;
- outcome relevance to aging.

A null knockdown and a positive catalytic inhibitor result are conflicting
operations, not automatic replication of one normalized link.

### Biological transfer

- donor/source and recipient definitions;
- transfer procedure and control;
- recipient assignment;
- compositional specificity;
- co-transferred material and interference;
- timing and recipient outcome.

Transfer identifies the effect of the transferred package. It does not identify
an individual microbe, molecule, or circulating factor without another design.

### Genetic instrument

- instrument relevance and strength;
- independence/LD handling;
- exclusion restriction and pleiotropy;
- directionality;
- population and sample overlap;
- ancestry and tissue relevance;
- heterogeneity and robust estimators;
- colocalization where the molecular proxy requires it;
- replication.

The interpretation is a genetically proxied exposure effect under IV
assumptions, not the effect of a drug, cessation, or short-term intervention.

### Mediation

- exposure precedes mediator and outcome;
- exposure-outcome exchangeability;
- exposure-mediator exchangeability;
- mediator-outcome exchangeability;
- no exposure-induced mediator-outcome confounder;
- interaction handling;
- direct and indirect estimands;
- sensitivity analysis.

Randomized exposure alone does not identify mediation. Cross-sectional
decomposition without the relevant assumptions is usually
`formal_hypothesis_only`.

For mediation fitted with SEM, `mediation_analysis` is the primary method and
`sem` is supporting. SEM is primary only when the annotated output is a broader
structural relation rather than a mediated effect.

### Temporal, structural, and discovery methods

- temporal spacing and lag definition;
- stationarity where required;
- time-varying confounding;
- acyclicity and faithfulness;
- causal sufficiency/unmeasured confounding;
- Markov equivalence;
- edge-orientation basis;
- interventional, temporal, or instrumental anchors;
- stability and external checks.

A directed edge or statistically upstream variable is not an effect estimate.
Invariance or environment-based orientation uses
`invariance_or_environment_based_model`; it is not forced into a generic causal
discovery category.

## Result status

Code the observed result independently of the design:

- `supports_claim`;
- `null`;
- `conflicting_within_report`;
- `mixed_or_time_specific`;
- `not_reported`;
- `unclear`.

Null and conflicting results remain in the main claim ledger. Evidence level
describes the design and identification, not whether the result is positive.

## Multi-omics role

For each relevant layer, use one canonical molecular-layer value:

- `genomics`;
- `epigenomics_dna_methylation`;
- `epigenomics_chromatin_accessibility`;
- `transcriptomics_bulk`;
- `transcriptomics_single_cell`;
- `transcriptomics_spatial`;
- `proteomics`;
- `metabolomics`;
- `lipidomics`;
- `glycomics`;
- `microbiome_amplicon`;
- `microbiome_metagenomic`;
- `immunophenotyping_cytomics`;
- `other_omics`.

QTL provenance is recorded separately as `eqtl`, `pqtl`, `mqtl`, `sqtl`, or
`none`; it is not embedded in a layer name. Network-pharmacology databases,
survival assays, targeted qPCR, immunoblotting, and imaging are not omics
layers.

Code one or more roles:

- `exposure_measure`;
- `instrument_source`;
- `candidate_nominator`;
- `mediator_candidate`;
- `outcome_measure`;
- `effect_modifier`;
- `mechanistic_localization`;
- `perturbation_readout`;
- `validation_only`;
- `composite_index_input`.

Targeted qPCR, western blot, ELISA, immunostaining, or a single-analyte assay is
not a new discovery-scale omics layer.

## Validation and Level 4

First record `validations_proposed_by_report` as `none`, `one_or_more`, or
`unclear`. `one_or_more` requires at least one validation record; an empty
array therefore cannot mean both "none" and "not extracted".

Every proposed validation is coded on separate dimensions:

- `validation_type`: `independent_same_link_replication`,
  `orthogonal_same_link_identification`, `appropriate_colocalization`,
  `measurement_confirmation`, `related_mechanism`, or `plausibility`;
- `same_link_alignment`: `exact`, `partial`, `related_mechanism`, `none`, or
  `unclear`;
- `operation_alignment`: `same`, `orthogonal`, `different`, or `unclear`;
- `data_independence`: `independent`, `partially_independent`,
  `not_independent`, or `unclear`;
- `experimental_independence`: the same four values;
- validation purpose: identification, mechanism, prediction, measurement, or
  general plausibility;
- result status.

Same-link comparison requires the same exposure construct, outcome, direction,
system target, and time horizon. Operation is recorded separately so a
prespecified orthogonal perturbation can validate the same biological link.
A change from molecular clock to lifespan or from a treatment to an unrelated
gene remains partial or related-mechanism alignment.

Python derives Level 4; reviewers never set a qualification flag. A positive
validation qualifies only through one of these frozen paths:

1. independent same-link replication with exact alignment, the same operation,
   independent data, and independent experiment;
2. orthogonal identification of the same link with exact alignment, an
   orthogonal operation, independent data, and an independent experiment;
3. appropriate colocalization of the exact molecular-proxy link when the Level
   3 claim is genetic-instrument evidence and the report states and meets its
   colocalization threshold.

All paths require `purpose=identification` and `result_status=supports_claim`.
An `unclear` input relevant to a potentially qualifying path routes Level 4
qualification to manual review. An unclear field that is not used by that path,
such as a colocalization threshold on a replication experiment, does not.
Internal robustness, another assay of the same sample, general pathway
plausibility, or a related outcome does not qualify.

## Frozen Level 1-4 mapping

The model or annotator records atomic fields; deterministic logic assigns the
candidate level:

| Reviewer assessment | Candidate level |
| --- | ---: |
| `no_identification` | 1 |
| `formal_hypothesis_only` | 2 |
| `effect_claim_not_assessable` with an eligible design method | 2 |
| `effect_claim_not_assessable` with prediction, prioritization, none, or unclear as primary method | 1 |
| `effect_assessable` | 3 |
| `effect_assessable` plus qualifying independent same-link validation | 4 |
| `unclear` | manual review |

Levels remain internal appraisal labels. They are not PRISMA categories or
paper-level quality scores.

Eligible Level 2 design methods are assigned interventions, quasi-experiments,
targeted perturbations, biological transfer, genetic instruments, mediation,
temporal models, DAG/SCM, SEM, Bayesian networks, causal discovery,
invariance/environment-based models, and `other_formal_design`.

`formal_hypothesis_only` requires an output that is a direction, mediated path,
temporal ordering, structural relation, or discovered edge. Fine-mapping
posterior ranks, colocalization-only results, network centrality, docking, and
other candidate ranking are `no_identification`, even when authors call the
ranked feature causal.

## Evidence contract

Every decisive field requires:

- a `source_adequacy` classification (`full_text`, `abstract_or_preview_only`,
  `proceedings_abstract`, `partial`, or `unclear`) and available-section list;
- the canonical deterministic Markdown path;
- the nearest preceding Markdown heading or stable section identifier;
- a shortest exact quotation that preserves the full logical polarity and is
  sufficient to support the coded field;
- an optional note explaining how the quotation supports the field.

`field_anchors` must reference evidence for author claim type, primary method,
variation sources, assignment, reviewer assessment, result status, estimand,
and all contrast components. Exact substring presence is necessary but not
sufficient; a fragment that drops negation or reverses polarity is invalid.

Abstract claims do not override contradictory Results, Methods, or Limitations.
For proceedings, the evidence must belong to the focal titled abstract.
An abstract/preview-only, partial, or unclear source yields
`reviewer_identification_assessment=unclear` until a full source is obtained.

## Prohibited shortcuts

- Do not infer identification from the words `causal`, `driver`, `mediates`, or
  `rejuvenation`.
- Do not infer a second omics layer from targeted validation assays.
- Do not infer mediation from post-intervention molecular change.
- Do not infer a drug effect from an MR estimate.
- Do not infer organismal rejuvenation from a clock or molecular-signature
  shift.
- Do not count a related mechanism as independent same-link validation.
- Do not merge conflicting exposure operations because they share a target
  name.
- Do not treat candidate ranking or fine-mapping as a directed causal
  hypothesis.
- Do not annotate a stronger claim that the report explicitly declines to
  make; normalize the claim to the report's actual assertion.

## Pilot acceptance questions

The v0.2.0 pilot must establish whether two reviewers can consistently:

1. segment reports into claims;
2. distinguish author claim from reviewer identification assessment;
3. select one primary design and link-specific sources of variation;
4. separate assessability from credibility limitations;
5. retain null and conflicting results;
6. normalize exposure operations for same-link validation;
7. apply Levels 1-4 without relying on graph labels;
8. detect partial sources before scientific coding;
9. complete every design-specific assumption domain;
10. exercise both positive and negative Level 4 paths.
