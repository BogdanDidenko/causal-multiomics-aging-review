# Table and figure specification

## Data units

All displays must preserve four linked identifiers:

`report_id -> study_or_cohort_id -> causal_analysis_id -> normalized_causal_link_id`

Counts must state their unit explicitly. A report count must never be labeled as
a study, cohort, analysis, or causal-link count.

## Main tables

### Table 1. Evidence landscape

`Domain | Category | Reports n (%) | Distinct studies/cohorts n | Causal analyses n | Normalized links n | Missing/unclear n`

Place evidence function and design family before omics combinations. State that
multi-label percentages may exceed 100%.

### Table 2. Directed discovery evidence

`Report ID | Population/model and aging construct | Omics layers and analytic connection | Discovery method and orientation constraints | Directed hypothesis (X -> Y) | Stability/robustness checks | External validation | Interpretation boundary`

### Table 3. Causal-effect evidence

`Report ID | Population/model (n, tissue, ancestry/sex) | Design family | Exposure/intervention/instrument -> outcome | Omics layers and integration point | Estimand/contrast and effect estimate (CI) | Identification assumptions/diagnostics | Sensitivity/negative controls | Validation/replication`

### Table 4. Link-level triangulation

`Causal-link ID | Aging construct/system | Normalized link | Discovery evidence | Effect evidence/design/estimate | Validation type/source | Participant/data independence | Concordance or discordance | Remaining limitation`

### Table 5. Design-specific credibility summary

`Design family | Appraisal domain | Assessable n | Low concern n/N | Some concerns n/N | High concern n/N | Not assessable n | Recurrent reason`

Complete claim-level versions of Tables 2-4 belong in machine-readable
supplements. The print article should aggregate prespecified cells rather than
selecting only representative positive reports.

## Main figures

### Figure 1. PRISMA 2020 flow

Retain the frozen full-text panel: 162 sought, 4 not retrieved, 158 assessed, 57
excluded, and 101 full-text eligible for causal evidence extraction. Do not call
the 101 reports final synthesis inclusions. Replace the provisional upstream
panel only after the complete PRISMA denominator is frozen.

### Figure 2. Design-first evidence landscape

- Panel A: counts by causal design family, split into discovery and effect.
- Panel B: design-family by aging-construct heatmap.
- Panel C: UpSet plot of omics combinations, stratified by evidence function.

Put tissue, model-system, and population distributions in supplementary panels
unless they are central findings.

### Figure 3. Causal-link triangulation map

Use one row per normalized causal link and three principal columns:

`Directed discovery | Identified effect | Independent validation`

The main figure may show links occupying at least two columns, provided the
complete map is published online. Encode direction, uncertainty, data-source
overlap, and validation independence explicitly.

### Figure 4. Credibility profile

Use design-family small multiples with explicit `n/N` for assumption reporting,
diagnostics, sensitivity or negative controls, independent validation,
data-source overlap, and transportability. Do not calculate an overall quality
score.

## Validation rules for displays

- Internal resampling or same-dataset sensitivity is not independent validation.
- Cross-omics agreement alone is not independent validation.
- Colocalization supports a genetic link but is not standalone effect
  identification.
- Repeated MR using overlapping exposure or outcome GWAS is not independent
  replication.
- Validation of another edge in the same pathway is not validation of the
  normalized link.
- Concordant animal or cell evidence must be labeled as cross-system support,
  not automatic confirmation of a human effect.
