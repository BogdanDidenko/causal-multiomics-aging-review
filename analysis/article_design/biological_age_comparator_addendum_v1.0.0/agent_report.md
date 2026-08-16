# Comparator report: Measuring biological age using omics data

## Bottom line

The article does not change the review's primary hierarchy:

`causal discovery -> causal-effect evidence -> independent validation of the same causal link`

It supplies a secondary taxonomy describing what biological-aging construct is
measured, at what scale, over what time frame, and for what intended use. The
article's own `Understanding correlation and causation` section states that
current aging clocks are correlational statistical models. They may generate
testable hypotheses, but do not identify causal effects without an additional
causal design.

The complete NIH author manuscript was examined in HTML and in equivalent BioC
XML and JSON representations.

## Narrative architecture

| Article element | Narrative function |
|---|---|
| Abstract and unheaded opening | Frames biological-age measurement as a geroscience problem; introduces predicted age, age gap, and age acceleration. |
| `Omic clocks` | Descriptive survey organized by molecular modality, not design or evidence strength. |
| `DNA methylation` | Progresses from chronological-age prediction to phenotype-trained and longitudinal measures; notes uncertain mechanism and tissue limitations. |
| `Transcriptomics` | Emphasizes interpretability and experimental testability, but also noise, small samples, platform variation, and weak external validation. |
| `Proteomics` | Presents proteins as interpretable and druggable while noting organ-function confounding, incomplete coverage, and limited validation. |
| `Metabolomics` | Covers mortality and disease associations, analytical noise, modest phenotype effects, and mixed tissue signals. |
| `Other omics` | Briefly surveys glycomics, microbiome composition, and chromatin state, primarily through predictive or associational evidence. |
| `Comparing different clocks` | Shows limited concordance and argues that clocks may measure different aspects of aging. |
| `Future perspectives` | Organizes recommendations around application, molecular features, correlation versus causation, and moving beyond chronological age. |
| `Defining the application of ageing clocks` | Establishes heterogeneity across cells, tissues, organs, systems, and individuals. |
| `Ideal molecular features to measure ageing` | Discusses interpretability, testability, druggability, and absence of a biological-age ground truth. |
| `Understanding correlation and causation` | Explicitly separates clocks from causal mechanisms and proposes experimental and human-genetic follow-up. |
| `Moving beyond chronological age` | Distinguishes chronological-age clocks, phenotype/composite clocks, biology-informed clocks, age-free models, and longitudinal pace measures. |
| `Conclusions` | Reiterates biomarker and clinical promise while calling for target-specific, tissue-aware, longitudinal, and multi-omic models. |

This is a problem-to-modality-survey-to-design-principles narrative. It has no
systematic-review search, eligibility, selection, risk-of-bias, or
evidence-certainty method.

## Figures and box

- **Figure 1, Classes of ageing biomarkers:** conceptual progression from
  visible features and organ-function measures to hallmarks and omics clocks.
- **Figure 2, Machine-learning concepts:** tutorial on regression clocks, age
  residuals, dimensionality, and neural networks.
- **Figure 3, Timeline 2008-2021:** selective field history; its caption states
  that it is not a complete evidence list.
- **Figure 4, Associations between age gaps and aging phenotypes:** compares
  phenotype sensitivity; it is an association display, not a causal-effect map.
- **Figure 5, Measuring aging across the body:** depicts between-person,
  between-organ, and within-tissue heterogeneity.
- **Box 1:** explains machine-learning families and interpretability, not causal
  identification.
- **Tables:** none.

## Conceptual partitions

### Biological age

The article defines biological age as biological functioning of an organism,
organ, or cell relative to expected functioning at a given chronological age.
The planned review should therefore extract the operational definition and
target scale instead of treating biological age as one interchangeable outcome.

### State versus pace

An age gap is a model residual or deviation from an age-specific expectation.
It is often interpreted as biological-age acceleration, but a cross-sectional
gap does not directly measure a future rate of aging. Distinguish:

- biological-age state;
- retrospective age gap;
- observed within-person change;
- estimated pace or rate;
- prospective clinical or survival outcome.

Repeated measurements improve temporal characterization but do not by
themselves identify a causal effect.

### Biological scale and source-to-target inference

Cells, tissues, organs, physiological systems, and whole organisms can age at
different rates. Blood, plasma, or skin measurements are often used as proxies
for other systems. Extract both the assayed source and claimed target, then
classify the match as direct, proxy, mixed-source, cross-system, or unclear.

### Clock role

A clock or biomarker can appear as an exposure, mediator, outcome, covariate,
discovery feature, or intervention-response endpoint. Its role in the causal
contrast must be explicit.

### Validation

The article uses validation broadly. The evidence map must distinguish:

- technical reliability;
- predictive generalization;
- construct or phenotype association;
- prognostic performance;
- intervention sensitivity;
- mechanistic feature testing;
- independent validation of the same normalized causal link.

Only the last category can satisfy the present Level 4 rule when Level 3 is
already established.

## Required additions to extraction

### Aging construct fields

- `aging_construct_class`: chronological age; biological-age state; pace/rate;
  mortality/lifespan/healthspan; clinical function/frailty; disease of aging;
  molecular hallmark/mechanism.
- `operational_definition_verbatim`.
- `temporal_target`: current state; retrospective gap; within-person change;
  future rate; time-to-event.
- `target_scale`: cell; tissue; organ; physiological system; whole organism;
  population.
- `assayed_biospecimen_or_tissue`.
- `claimed_target_tissue_or_system`.
- `assay_target_match`: matched; proxy; mixed-source biofluid; cross-system;
  unclear.
- `aging_measure_causal_role`: exposure; intervention; mediator; outcome;
  covariate; discovery feature; validation response.
- `causal_object`: exact relation being claimed.

### Conditional clock fields

- `clock_name_and_version`.
- `clock_input_omics`.
- `clock_training_target`: chronological age; mortality/survival; clinical
  composite; molecular/physiological phenotype; longitudinal pace; unsupervised.
- `clock_model_family`.
- `age_gap_definition_and_residualization`.
- `training_validation_overlap`.
- `cell_composition_or_mixture_handling`.
- `measurement_schedule_and_number_of_timepoints`.
- `clock_response_and_functional_outcome_reported_separately`.

### Validation fields

- `validation_target`.
- `validation_independence`: participants, datasets, laboratories, platforms,
  and analytic teams.
- `same_normalized_link`: yes; no; partial.
- `cross_population_tissue_species_status`.
- `clinical_intended_use`.
- `incremental_utility_or_surrogate_evidence`.

## Manuscript changes

### Introduction

Refine the opening concept to **biological aging as a multi-scale,
multi-temporal construct and cross-layer causal problem**. Define:

1. chronological age versus biological functioning;
2. state versus pace of change;
3. cell, tissue, organ, system, and organism targets;
4. predictive biomarker, causal determinant, mediator, outcome, and
   intervention-response roles.

Add the guardrail that chronological-age prediction, age-gap association,
longitudinal change, intervention responsiveness, and causal-effect
identification answer different questions.

### Results

Within the design-first evidence landscape, add a subordinate section on
**biological-aging constructs and measurement targets**. Report state versus
pace versus event/function, target scale, source-to-target match, training
target, cross-sectional versus longitudinal measurement, causal role, and
validation purpose.

Do not create modality-first Results sections for methylation,
transcriptomics, proteomics, and metabolomics.

### Credibility and gaps

Add age-gap operationalization, target-tissue mismatch, cell composition,
mixed-biofluid ambiguity, cross-sectional selection or survivor bias, circular
validation against training variables, absence of functional outcomes alongside
clock change, and unsupported surrogate-endpoint interpretation.

### Discussion

State explicitly:

1. measurement validity is not causal validity;
2. biological age is plural and scale-dependent;
3. intervention sensitivity is endpoint-specific.

Prioritize repeated-measures causal designs, tissue-matched perturbations,
independent same-link validation, and trials reporting both clock and
functional or clinical outcomes.

## Display changes

### Main tables

- Table 1: add aging construct, temporal target, target scale,
  assayed-to-claimed system match, clock training target, and validation target.
- Table 2: expand the population/model column to include aging construct,
  temporal target, biological scale, and clock/biomarker role.
- Table 3: add `assayed source -> claimed target system` and keep clock response
  separate from functional or clinical outcome.
- Table 4: expand the aging-system field with temporal target, biological scale,
  and measurement role.
- Table 5: add conditional construct-validity, temporal-adequacy,
  source-to-target, and outcome-circularity domains without a summed score.

### Main figures

- Figure 2B: partition aging constructs into state, pace/rate, and
  event/function; annotate target scale.
- Figure 3: annotate whether the clock is exposure, mediator, outcome, or
  intervention response. Do not add generic clock validation as a fourth causal
  evidence column.
- Figure 4: add source-to-target match, temporal adequacy, and independence from
  clock-training data.

### Supplementary displays

1. Biological-aging measure dictionary: operational definition, input omics,
   training target, temporal type, assayed source, claimed scale, and causal role.
2. Validation audit: validation target, same-link status, independence,
   tissue/species match, supported interpretation, and unsupported
   interpretation.
3. Measurement-target heatmap: temporal construct by biological scale, faceted
   by training target and stratified by evidence function.
4. Source-to-target transport map: assayed tissue or biofluid to claimed
   biological target.

## Structural choices not to import

- Omics modality as the primary Results hierarchy.
- First- versus second-generation clocks as a quality or causal ranking.
- The selective timeline as a corpus map.
- Positive illustrative studies without denominator-based synthesis.
- Age-prediction accuracy as biological or causal validity.
- Cross-clock concordance as causal-link validation.
- Proteomic primacy, druggability, or universal-ageometer speculation as review
  conclusions.
- Animal or cellular rejuvenation as automatic confirmation of a human effect.
- Precision-medicine or surrogate-endpoint claims without direct utility
  evidence.

The comparator is itself ineligible for the causal synthesis because it is a
narrative review rather than primary empirical research. Primary clock studies
that offer only prediction or association remain associational; they must also
meet the current report's multi-omics boundary.

## Overclaiming guardrails

| Observation | Maximum defensible interpretation without an additional causal design |
|---|---|
| Accurate chronological-age prediction | Predictive performance, not biological or causal validity. |
| Age gap associated with mortality or disease | Prognostic or construct association. |
| Biomarker changes with age | Cross-sectional or longitudinal association, not an aging driver. |
| Clock changes after an intervention | Endpoint responsiveness; potentially an intervention effect on the clock if assignment supports it. |
| Clock becomes younger | Biomarker shift, not necessarily organismal rejuvenation. |
| Response in a longevity mutant or restricted animal | Convergent validity, not proof that clock features cause longevity. |
| Independent-cohort replication | Predictive validation, not automatically causal-link validation. |
| Cross-omics agreement | Measurement convergence, not independent causal validation. |
| Longitudinal clock | Better temporal characterization, not causal identification by itself. |
| Feature importance or model weight | Model contribution, not a causal effect. |
| Colocalization | Genetic-link support, not standalone effect identification. |
| MR with assessable assumptions and diagnostics | Potential causal-effect evidence for the specified contrast. |
| Functional perturbation of one clock feature | Potential validation of that exact feature-to-outcome link, not the whole clock. |
| Mortality-trained clock predicts mortality | Possibly expected performance; training overlap and circularity require assessment. |
| Intervention-sensitive clock proposed as a trial endpoint | Candidate pharmacodynamic biomarker, not a qualified surrogate endpoint. |

## Final decision

Retain evidence function and causal design family as the primary axis. Add:

`aging construct x temporal target x biological scale x clock role x validation target`

as the secondary measurement axis. This preserves the distinction between what
is measured, how it predicts, and which causal relation is actually identified.
