# Independent full-text reviews

## 1. Methodology and appraisal

### Comparator findings

The AMD review provides a conventional systematic-review shell: PRISMA 2020,
PubMed and Scopus searches, OHAT risk-of-bias assessment, a standardized
33-report table, and a separate biological synthesis. Its structure is readable,
but OHAT alone cannot appraise the mixed causal designs expected in the present
review. Mendelian randomization, mediation, perturbation, temporal designs, and
causal discovery have different identification assumptions and diagnostics.

Kerr et al. provide stronger review governance: a published protocol, JBI
guidance, PCC framing, PRISMA-ScR, broad sources, duplicate extraction, third
reviewer adjudication, field mapping, and thematic synthesis. Their generic
high/medium/low critical-appraisal categories are still too coarse for a
causal-design review.

### Recommendation

Appraise causal claims, not only reports. Do not calculate one cross-design
quality score. Preserve four parallel dimensions:

1. effect-specific risk of bias or identification credibility;
2. credibility of directed discovery;
3. validity of multi-omics integration;
4. independence and transportability of validation.

Use conditional modules for randomized interventions, non-randomized
interventions, perturbations, Mendelian randomization and other instruments,
mediation, temporal identification, DAG/SCM/SEM models, Bayesian networks, and
formal causal-discovery algorithms.

Colocalization is support for a genetic causal link, not an identification
strategy by itself. An RCT treatment effect does not automatically identify
molecular mediation. A molecular perturbation does not automatically establish
a population-level genetic effect.

## 2. Results, tables, and figures

### Comparator findings

The AMD review moves through study characteristics, quality assessment, and a
setting-first synthesis: non-clinical evidence subdivided into risk factors,
early disease, advanced disease, and treatment, followed by clinical local and
systemic evidence. Its nine-column study table spans about five pages for only
33 reports, so the format will not scale to the current candidate corpus.
Causal designs are buried in `Assay type` or `Main findings`, mixing association,
perturbation, and effect estimation.

Kerr et al. provide the better field-map scaffold. Their aggregate tables show
study characteristics, fourteen omics combinations, participant phenotypes, and
disease categories. Five themes discovered in Results become Discussion
headings, and a final workflow converts observed heterogeneity into a research
agenda. However, their design categories are not causal-design categories.

### Recommendation

Maintain four linked units:

`report_id -> study_or_cohort_id -> causal_analysis_id -> normalized_causal_link_id`

The normalized link must identify the exposure, intervention, or instrument;
outcome; direction; aging construct; and biological system. This avoids counting
reused cohorts, multiple analyses, or multiple causal links as independent
reports.

Use design-first aggregate displays in the article and place the complete
claim-level ledger online. Avoid a 101-row print table, an omics-first Results
section, a dense alluvial diagram, and any mechanism diagram that visually gives
all arrows equal causal status.

## 3. Scientific narrative

### Comparator findings

The strongest reusable pattern is Kerr's progression from quantitative mapping
to declared themes and then to a prescriptive workflow, combined with the AMD
review's second-pass biological interpretation. The present article must add an
inferential boundary absent from both comparators.

### Recommendation

Use this narrative progression:

1. map the eligible corpus and data dependencies;
2. describe formal directed hypotheses;
3. describe assessable causal effects by identification strategy;
4. examine independent validation of the same links;
5. only then synthesize recurrent mechanisms of aging;
6. close with credibility, reporting, and transportability gaps.

Suggested title: *Causal discovery and causal-effect evidence in multi-omics
studies of biological aging: a systematic evidence map*.

Target about 7,000-7,500 words in the main text, excluding abstract,
references, displays, and supplementary material. Keep operational AI-screening
detail concise in the article and preserve the full prompts, five-run outputs,
stability measures, and human adjudications in supplements.

## 4. Skeptical peer review

### Main risks

- The current 101 eligible reports are not necessarily 101 independent studies,
  cohorts, causal analyses, causal links, or final synthesis inclusions.
- Reuse of UK Biobank, FinnGen, GTEx, and other public resources can create false
  replication if data-source overlap is not tracked.
- Aging phenotypes are heterogeneous; chronological age, biological-age
  acceleration, senescence, lifespan, frailty, rejuvenation, and age-related
  disease cannot be treated as interchangeable outcomes.
- Biological coherence and cross-omics agreement can masquerade as causal
  validation.
- Repeated-run model agreement measures reproducibility of the screening
  instrument, not scientific accuracy.

### Claims to avoid

- Multi-omics integration itself establishes causality.
- Colocalization alone establishes an effect.
- A directed network edge is an identified effect.
- A sensitivity analysis in the same data is independent validation.
- A related edge, pathway, tissue, or reused cohort validates the same causal
  link.
- Animal or cell evidence automatically proves a human aging effect.
- Five-run agreement validates the eligibility decision.
- The review is the first of its kind without an updated review-focused search.

### Mandatory safeguards

Link reports to studies and data sources; stratify aging constructs; build a
claim ledger; apply design-specific appraisal; preserve null and discordant
evidence; and report model instability and human overrides explicitly.
