# Claim-level causal identification codebook v0.1.0

## Status and purpose

This is an instrument-development draft for causal evidence extraction from the
101 full-text-eligible reports. It does not change eligibility, PRISMA counts,
the active full-text prompts, or the frozen Levels 0-4 rules.

The codebook separates factual extraction from review judgment. Its purpose is
to prevent a named method, an author causal verb, or a model-generated graph
label from being treated as sufficient evidence of causal identification.

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

## Four core fields

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
- `predictive_or_associational_model`;
- `computational_prioritization`;
- `other_formal_design`;
- `none`;
- `unclear`.

Supporting methods are recorded separately. Method names do not determine the
evidence level.

### 3. `source_of_identifying_variation`

Record what creates the exposure contrast used for the claim:

| Value | Typical examples |
| --- | --- |
| `randomized_assignment` | Random allocation to intervention or control. |
| `investigator_assigned_exposure` | Controlled treatment without documented randomization. |
| `engineered_or_targeted_perturbation` | Knockout, knockdown, overexpression, CRISPR, or target-directed inhibitor. |
| `transferred_biological_material` | FMT, parabiosis, plasma, cells, or other transferred material. |
| `inherited_genetic_variation` | Valid genetic instrument in MR/IV analysis. |
| `quasi_exogenous_rule_or_event` | Threshold, policy, natural experiment, or other plausibly exogenous assignment. |
| `within_unit_temporal_variation` | Repeated observations or lagged change without another exogenous source. |
| `observational_covariation` | Unassigned between-person, between-tissue, or between-feature variation. |
| `none` | Prediction or prioritization with no identifying contrast. |
| `unclear` | Source cannot be established from the available text. |

This field describes provenance of the contrast, not its validity. For example,
MR uses inherited variation even when exclusion restriction is not adequately
addressed.

### 4. `reviewer_identification_assessment`

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

## Required claim fields

Each claim record contains:

- report DOI and stable `claim_id`;
- normalized claim statement;
- exact exposure/intervention and `exposure_operation`;
- comparator;
- outcome;
- population/model and biological system;
- time horizon;
- `author_claim_type`;
- primary and supporting `design_or_method` values;
- `source_of_identifying_variation`;
- method output type;
- contrast/estimand statement and completeness;
- design-specific assumptions and diagnostics;
- `reviewer_identification_assessment`;
- result status;
- omics roles;
- validation records;
- Level 1-4 derived under the frozen policy;
- evidence anchors from the deterministic full text.

## Method output types

Use the most specific output represented by the claim:

- `total_effect`;
- `direct_or_controlled_effect`;
- `indirect_effect`;
- `necessity`;
- `sufficiency`;
- `rescue_or_epistasis`;
- `post_intervention_molecular_response`;
- `genetically_proxied_effect`;
- `temporal_ordering`;
- `directed_edge_or_structure`;
- `prediction`;
- `candidate_prioritization`;
- `other`;
- `unclear`.

Necessity, sufficiency, and rescue must not be collapsed. Pharmacologic
inhibition, transcript knockdown, protein depletion, and germline knockout are
different exposure operations even when they share a gene symbol.

## Contrast completeness

`contrast_complete=yes` requires all of the following:

1. exposure/intervention operation;
2. comparator or counterfactual contrast;
3. outcome;
4. population/model and system;
5. time horizon when relevant;
6. effect measure, contrast, or logical perturbation output.

Missing details are coded `no`; unavailable or ambiguous details are `unclear`.

## Design-specific assumption modules

Record each assumption as `addressed`, `not_reported`, `violated`,
`not_applicable`, or `unclear`, with an evidence anchor.

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

For each relevant layer, code one or more roles:

- `exposure_measure`;
- `instrument_source`;
- `candidate_nominator`;
- `mediator_candidate`;
- `outcome_measure`;
- `effect_modifier`;
- `mechanistic_localization`;
- `perturbation_readout`;
- `validation_only`.

Targeted qPCR, western blot, ELISA, immunostaining, or a single-analyte assay is
not a new discovery-scale omics layer.

## Validation and Level 4

Every proposed validation is coded on separate dimensions:

- `same_link_alignment`: `exact`, `partial`, `related_mechanism`, `none`, or
  `unclear`;
- `data_independence`: `independent`, `partially_independent`,
  `not_independent`, or `unclear`;
- `experimental_independence`: the same four values;
- validation purpose: identification, mechanism, prediction, measurement, or
  general plausibility;
- result status.

Same-link comparison requires exposure identity, exposure operation, outcome,
direction, system target, and time horizon to be explicitly compared. A change
from inhibitor to knockdown or from molecular clock to lifespan is at most
partial alignment until justified.

Level 4 requires a Level 3 claim plus materially independent evidence aligned
to the same operationalized causal link. Internal robustness, colocalization
alone, another assay of the same sample, general pathway plausibility, or a
related outcome does not qualify.

## Frozen Level 1-4 mapping

The model or annotator records atomic fields; deterministic logic assigns the
candidate level:

| Reviewer assessment | Candidate level |
| --- | ---: |
| `no_identification` | 1 |
| `formal_hypothesis_only` | 2 |
| `effect_claim_not_assessable` with a formal directed/design basis | 2 |
| `effect_claim_not_assessable` without a formal basis | 1 |
| `effect_assessable` | 3 |
| `effect_assessable` plus qualifying independent same-link validation | 4 |
| `unclear` | manual review |

Levels remain internal appraisal labels. They are not PRISMA categories or
paper-level quality scores.

## Evidence contract

Every decisive field requires:

- the canonical deterministic Markdown path;
- a section heading or stable section identifier;
- a shortest exact quotation;
- an optional note explaining how the quotation supports the field.

Abstract claims do not override contradictory Results, Methods, or Limitations.
For proceedings, the evidence must belong to the focal titled abstract.

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

## Pilot acceptance questions

The v0.1.0 pilot must establish whether two reviewers can consistently:

1. segment reports into claims;
2. distinguish author claim from reviewer identification assessment;
3. select one primary design and source of identifying variation;
4. separate assessability from credibility limitations;
5. retain null and conflicting results;
6. normalize exposure operations for same-link validation;
7. apply Levels 1-4 without relying on graph labels.
