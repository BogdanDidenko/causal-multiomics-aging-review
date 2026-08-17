# Working article structure synthesis v1.1.0

## Status

This is the next working architecture for the review article. It integrates the
full-text analyses of the AMD systematic review, the Kerr rare-disease scoping
review, the Rutledge biological-age narrative review, and the four independent
methodology, display, editorial, and red-team analyses.

It does not change screening eligibility or the current PRISMA denominator. It
should be frozen only after claim-level causal extraction shows the actual
distribution of design families and evidence strata.

## Article identity

**Recommended article type:** systematic review and evidence map with
claim-level causal appraisal.

**Working title:**

> Causal discovery and causal-effect evidence in multi-omics studies of
> biological aging: a systematic review and evidence map

The paper is science-first. AI-assisted screening is reported transparently as
part of the review method and audit trail, but is not the primary scientific
story.

## Core conceptual refinement

The earlier three-part narrative remains useful:

`discovery -> causal effects -> validation`

The formal data model should be more precise:

1. **Primary evidence stratum: causal hypothesis/discovery.** A formal directed
   method produces a testable causal hypothesis, but an assessable causal effect
   is not identified.
2. **Primary evidence stratum: causal-effect evidence.** A design supports an
   assessable causal contrast in a specified biological system.
3. **Cross-cutting validation layer.** Internal robustness, external predictive
   validation, same-link replication, orthogonal perturbation, and cross-system
   support are coded separately rather than treated as a mutually exclusive
   third study type.

This matches the internal levels:

- Level 2: causal hypothesis/discovery;
- Level 3: assessable causal effect;
- Level 4: Level 3 plus independent validation of the same causal link.

Validation may also strengthen a directed hypothesis without converting it into
an identified effect. Predictive validation must never be counted as causal-link
validation automatically.

## Review questions

1. Which aging constructs, biological systems, omics combinations, and
   integration architectures have been examined using formal causal methods?
2. Which directed causal hypotheses have been generated, by which formal
   methods, and with what stability or external support?
3. Which assessable causal effects have been reported, for which estimands and
   under which identification assumptions and diagnostics?
4. How do different omics layers participate in the causal analysis as
   exposures, instruments, mediators, outcomes, discovery features, or
   validation measurements?
5. Which normalized causal links have been independently replicated or tested
   using orthogonal designs, data, tissues, systems, or species?
6. Where are the main credibility, reporting, data-dependence, and
   transportability gaps?

## Units of analysis

Maintain four linked units:

`report_id -> study_or_cohort_id -> causal_analysis_id -> normalized_causal_link_id`

The article must state the unit behind every number. The current 101 records are
full-text-eligible reports entering causal extraction, not 101 independent
studies or final synthesis inclusions.

A normalized causal link includes:

- exposure, intervention, instrument, or source node;
- outcome or target node;
- direction;
- aging construct and temporal target;
- biological scale and system;
- population or model;
- causal estimand or directed-hypothesis meaning.

## Evidence-map coordinate system

Each causal analysis is mapped on five orthogonal axes:

1. **Evidence stratum:** discovery/hypothesis or causal effect.
2. **Design family:** genetic instrument, intervention, perturbation, mediation,
   temporal design, DAG/SCM/SEM, Bayesian network, or formal causal discovery.
3. **Multi-omics role:** layers used as exposure, instrument source, mediator,
   outcome, joint discovery input, mechanistic localization, or validation.
4. **Aging measurement:** construct, state versus pace/event, temporal target,
   assayed source, claimed biological scale, and clock role.
5. **Credibility and validation:** assumptions, diagnostics, sensitivity checks,
   data overlap, independence, same-link match, and transportability.

This avoids forcing omics modality, biological mechanism, and inferential
strength into one hierarchy.

## Narrative thesis

The article should answer one central question:

> When multi-omics aging studies use causal language or formal causal methods,
> what causal claim is actually supported, in which biological system, and how
> independently has that same claim been tested?

The Results should move from field map to inferential function, then to
same-link validation, and only afterward to biological mechanisms.

## Proposed manuscript architecture

### Structured abstract

- Background: biological aging is multi-scale, but multi-omics integration does
  not itself identify causality.
- Objective: map formal causal hypotheses, identified effects, and validation.
- Methods: databases, frozen eligibility, claim-level units, design-specific
  appraisal, and audited AI-assisted screening.
- Results: report discovery and effect strata separately; distinguish full-text
  eligibility from final synthesis counts.
- Conclusion: state what is hypothesis-level, effect-supported, and independently
  tested.

### 1. Introduction

#### 1.1 Biological aging as a multi-scale, multi-temporal construct

Define chronological age, biological-age state, pace/rate, lifespan or
healthspan, functional aging, senescence, and age-related disease. Explain that
cells, tissues, organs, systems, and organisms may not age synchronously.

#### 1.2 What multi-omics can add

Explain cross-layer mediation, mechanistic localization, directed discovery,
and triangulation. Avoid implying that more layers automatically produce
stronger inference.

#### 1.3 Prediction, direction, and causal identification are different

Separate age prediction, association, feature importance, directed network
edges, causal-effect identification, and independent validation. Use aging
clocks as a motivating boundary case rather than a separate review topic.

#### 1.4 Review gap and objectives

Explain that previous reviews map omics technologies or aging biomarkers but do
not systematically classify what causal claim each multi-omics design supports.

### 2. Methods

#### 2.1 Protocol, reporting, and amendments

Report registration, PRISMA framework, search dates, protocol versions, and
deviations. Keep the superseded pilot separate from the final denominator.

#### 2.2 Eligibility and units

State the aging, multi-omics, empirical-report, and formal-causal-method
boundaries. Define report, study/cohort, causal analysis, and normalized link.

#### 2.3 Search, deduplication, retrieval, and selection

Provide database-native strategies, branch counts, DOI and title deduplication,
full-text retrieval, reasons not retrieved, and criterion-level exclusions.

#### 2.4 AI-assisted screening and audit

Describe model/version, five independent runs, deterministic packaging,
criterion-level schemas, quotation grounding, unanimous-exclusion rule, retry
policy, and human adjudication. Make clear that stability measures
reproducibility, not accuracy.

#### 2.5 Claim-level extraction

Extract population/model, sample/data source, aging construct, temporal target,
biological scale, tissue, omics layers, integration role, causal claim, design
family, estimand, assumptions, diagnostics, sensitivity analyses, result,
validation target, and validation independence.

#### 2.6 Evidence classification

Classify the claim, not the paper or method name, into causal discovery or
causal-effect evidence. Code validation separately. Explain the internal Levels
0-4 only as an implementation of these decisions.

#### 2.7 Design-specific credibility appraisal

Use conditional domains for genetic instruments, randomized and
non-randomized interventions, perturbations, mediation, temporal designs,
structural models, Bayesian networks, and causal-discovery algorithms. Do not
calculate one cross-design quality score.

#### 2.8 Synthesis

Describe report linkage, shared-data handling, denominator rules, normalized
link matching, narrative synthesis, and why statistical pooling is or is not
appropriate.

### 3. Results

#### 3.1 Study selection and analytic corpus

Present the final PRISMA flow and the transition from reports to distinct
studies/cohorts, causal analyses, normalized links, and final synthesis units.

#### 3.2 Evidence landscape and multi-omics integration roles

Map evidence stratum and design family first. Then show aging constructs,
biological scales, tissues, omics combinations, integration timing and roles,
population/model distributions, and shared data sources.

This section answers what was studied and how multi-omics entered the causal
analysis; it does not yet interpret individual biological mechanisms.

#### 3.3 Formal causal hypotheses and discovery

Report directed hypotheses, discovery family, orientation constraints,
stability, internal robustness, and external support. Explicitly distinguish
an oriented edge from an effect estimate.

#### 3.4 Causal-effect evidence by identification strategy

Organize by:

1. genetic instruments;
2. randomized, quasi-experimental, and direct perturbation designs;
3. temporal, mediation, and structural effect designs.

For every family, report the estimand or contrast, biological system,
assumptions, diagnostics, sensitivity analyses, effect direction, uncertainty,
and data dependencies.

#### 3.5 Validation and triangulation of normalized links

Report validation as an overlay on discovery and effect evidence. Separate:

- internal robustness;
- external predictive validation;
- independent replication of the same effect;
- orthogonal perturbation of the same link;
- cross-tissue, cross-system, or cross-species support;
- conflicting or null validation.

Require an explicit same-link judgment and data-independence assessment.

#### 3.6 Aging mechanisms across evidence strata

Only now synthesize recurrent mechanisms. For each mechanism, show discovery
hypotheses, effect-supported links, validation, relevant biological scale, and
discordant evidence side by side.

Do not let pathway coherence, cross-omics agreement, or a related edge
masquerade as validation of the focal link.

#### 3.7 Credibility, reporting, and transportability gaps

Summarize missing assumptions, diagnostics, negative controls, sensitivity
analyses, replication, ancestry/sex reporting, tissue mismatch, clock-training
circularity, data overlap, model-system limitations, and unsupported clinical
or rejuvenation claims.

### 4. Discussion

#### 4.1 Principal findings

Describe the balance between directed hypothesis generation, assessable causal
effects, and independent same-link testing.

#### 4.2 What multi-omics actually adds

Discuss whether multi-omics enabled identification, mediation, localization,
mechanistic interpretation, or only broader measurement.

#### 4.3 What the evidence does and does not identify

Interpret pleiotropy, confounding, reverse causation, graph equivalence,
intervention specificity, temporal ambiguity, and model dependence.

#### 4.4 Biological-age measurement and causal interpretation

State that measurement validity is not causal validity; biological age is
scale- and time-dependent; and intervention sensitivity is endpoint-specific.

#### 4.5 Validation and transportability

Distinguish reproducibility, predictive generalization, same-link replication,
orthogonal support, mechanistic confirmation, and translation to humans.

#### 4.6 Design and reporting implications

Derive a workflow or checklist covering causal question, estimand, omics roles,
assumptions, diagnostics, source-to-target inference, data independence, and
prespecified validation.

#### 4.7 Strengths and limitations

Address search sensitivity, terminology, unavailable reports, report and data
dependence, heterogeneous designs, limits of pooling, AI-assisted screening,
and publication/reporting bias.

#### 4.8 Research agenda

Prioritize independent same-link replication, longitudinal and interventional
designs, tissue-matched perturbations, diverse populations, functional outcomes
alongside clock changes, and prospective validation.

### 5. Conclusion

Answer the review question using the two evidence strata and validation overlay.
Avoid claiming that multi-omics, directed networks, aging clocks, or biological
coherence establish causality by themselves.

## Display architecture

### Required main displays

1. **PRISMA flow:** records, reports, retrieval, eligibility, and final synthesis.
2. **Evidence-map framework:** the four linked units and five mapping axes.
3. **Design-first landscape:** evidence stratum by design family, aging
   construct, and multi-omics role.
4. **Normalized-link validation map:** discovery, effect, and validation status
   with data overlap and discordance visible.
5. **Design-specific credibility profile:** domain-level `n/N`, no total score.

### Main tables

1. Corpus and unit counts, with denominators for reports, studies/cohorts,
   analyses, and links.
2. Causal-effect evidence with estimand, system, omics role, assumptions,
   diagnostics, estimate, and validation.
3. Same-link triangulation and discordance summary.

The number of main displays should be adapted to the target journal. Complete
discovery, effect, validation, and appraisal ledgers belong in machine-readable
supplements rather than oversized print tables.

### Required supplements

- complete database strategies and search logs;
- deduplication and report-linkage ledger;
- eligibility decisions and exclusions;
- AI prompts, schemas, repeated-run outputs, stability metrics, and human
  overrides;
- extraction codebook and complete claim ledger;
- biological-aging measure dictionary;
- validation-independence audit;
- data-source overlap map;
- design-specific appraisal domains and judgments;
- evidence quotations and all null or discordant findings.

## What is borrowed from the comparator reviews

- **Kerr:** protocol governance, PCC-style clarity, quantitative map before
  themes, duplicate extraction, and map-to-theme-to-workflow narrative.
- **AMD:** standardized study characterization and second-pass biological
  synthesis after the evidence map.
- **Rutledge:** state-versus-pace distinction, multi-scale aging, source-to-target
  inference, clock roles, and the separation of predictive from causal validity.

## What is deliberately rejected

- one generic OHAT/JBI score across heterogeneous causal designs;
- omics modality as the primary Results hierarchy;
- report-level quality or evidence labels when claims differ within a paper;
- a long all-report table in the main article;
- a mechanism diagram in which all arrows appear equally causal;
- predictive validation as Level 4 causal validation;
- same-dataset sensitivity or overlapping public data as independent
  replication;
- aging-clock change as automatic functional rejuvenation;
- repeated-run model agreement as scientific validity.

## Decisions still dependent on extraction

Do not freeze mechanism subsections, final tables, or the number of main figures
until extraction establishes:

- counts by evidence stratum and design family;
- number of distinct cohorts and normalized links;
- prevalence of clocks and biological-age constructs;
- degree of data-source overlap;
- number of same-link replications and discordant results;
- whether any groups are sufficiently homogeneous for quantitative pooling.
