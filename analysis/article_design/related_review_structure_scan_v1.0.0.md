# Related-review structure scan v1.0.0

## Purpose and boundary

This scan supports article design. It is not a new identification search, does
not alter the frozen PRISMA denominator, and does not affect study eligibility.

The first pass inspected the 7,858 canonical records in
`data/normalized/v1.1.2/canonical_all_sources.csv`. A record was considered
review-like when its document type contained `review` or `meta-analysis`, or
its title/abstract explicitly described a systematic review, scoping review,
or evidence map. This produced 1,397 review-like records, of which 573 also
carried the local three-block retrieval signal. These fields are retrieval
metadata, not validated article types.

Fifty-one review-like records mentioned aging, multi-omics, and at least one
causal-method term in the title or abstract. Thirteen also contained a
systematic/scoping/meta-analysis/evidence-map signal. Manual checking showed
that most of these 13 were primary studies mislabeled as reviews, broad reviews
that only mentioned one target concept, or reviews of a materially different
question. No manually verified record reviewed the same intersection as the
current project: aging processes, analytically integrated molecular omics, and
formal causal discovery or causal-effect designs.

The shortlist is recorded in
`related_review_shortlist_v1.0.0.csv`. Eight of nine structural comparators
came from the original 7,858 records. One additional critical review of aging
clocks was added because its correlation-versus-causation structure is useful.

## Closest structural comparators

### 1. Systematic multi-omics review of age-related macular degeneration

[Castro-Fernandez et al. (2026)](https://doi.org/10.1016/j.survophthal.2026.02.001)
is the closest methodological comparator. It screened 561 records, included 33
reports, assessed study quality with the OHAT approach, and used standardized
evidence tables. Its structure is:

1. Introduction.
2. Results: study characteristics, quality assessment, and synthesis.
3. Non-clinical studies: risk factors, early processes, advanced processes,
   and treatment.
4. Clinical studies: local and systemic processes.
5. Discussion and conclusion.
6. Methods: search strategy, eligibility, quality of evidence, extraction, and
   synthesis.

Its two central outputs are a PRISMA figure and a 33-report evidence table. A
second figure maps convergence across omics layers onto inflammation,
angiogenesis, lipid dysregulation, and mitochondrial dysfunction. The design is
useful, but clinical/non-clinical is not the right primary split for the
current review.

### 2. Scoping review of multi-omics in rare disease

[Kerr et al. (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7189570/)
provides the strongest reusable methods scaffold. It defines the question with
PCC, follows PRISMA-ScR, performs duplicate data charting, applies a JBI-derived
critical appraisal, and conducts qualitative thematic synthesis. Its results
include:

- a PRISMA flow;
- general study characteristics;
- 14 observed combinations of omics layers;
- participant/disease distributions;
- themes organized by diagnostic, pathogenic/prognostic, and therapeutic use;
- a proposed workflow derived from the evidence.

This is a better model for transparent study mapping than the narrative aging
reviews, although its scientific question is not about aging or causal
identification.

### 3. Aging and cellular-senescence multi-omics reviews

[Basilicata et al. (2025)](https://doi.org/10.1016/j.arr.2025.102824)
is the closest biological-process comparator. It moves from senescence
mechanisms to proteomic, metabolomic, and lipidomic alterations, then ends with
the added value of multi-omics. It has no reproducible search or selection
section.

[Wu et al. (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8773837/)
uses the following hierarchy: chronological versus biological age, aging
clocks, biomarkers by omics layer, integromics/systems biology, and prospects.
It is useful for terminology and background but not as a systematic-review
template.

[Lorusso et al. (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6104250/)
surveys genomic, transcriptomic, translatomic, proteomic, epigenomic, and
metabolomic approaches before discussing data integration and open questions.
Its strongest transferable element is the explicit question of which molecular
changes are causes of aging and which are consequences.

[Kiseleva et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11677528/)
organizes evidence by cardiovascular, neurodegenerative, bone, and cancer
domains and uses disease-specific tables of omics combinations and findings.
This is preferable to a pure omics-by-omics catalogue for biological
interpretation, but it still mixes aging itself with age-related disease.

### 4. Causal interpretation comparators

[Suk (2026)](https://doi.org/10.1016/j.expneurol.2026.115737) evaluates
causality in brain aging through Bradford Hill considerations, longitudinal
evidence, genetic approaches, and senolytic trials. It also treats reciprocal
and feed-forward relationships explicitly. This is useful for the Discussion
and evidence interpretation, but it is neither systematic nor primarily a
multi-omics review.

[Rutledge et al. (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10048602/)
first maps omics-clock modalities, then shifts to application, comparison of
clocks, correlation versus causation, and validation. This question-led second
half is a useful model for avoiding a descriptive catalogue.

[Suryawan et al. (2026)](https://doi.org/10.4103/wkpj.wkpj_37_26) is the
closest lexical near-hit: it combines a systematic review, causal mechanisms,
multi-omic placental programming, and an evidence map. Its target question is
nevertheless developmental programming of later disease rather than biological
aging processes. It is therefore a useful comparator for mixed-design
triangulation, but not evidence that the current review question has already
been answered.

## Structural patterns and decision

Three recurring structures were observed:

1. **Omics-first narrative:** one section per molecular layer, followed by
   integration and future directions. This is common but would obscure the
   causal question.
2. **Disease/process-first narrative:** one section per organ, disease, or
   biological process. This is biologically readable but can mix association
   and causal evidence.
3. **Systematic evidence map:** PRISMA methods, study-characteristic tables,
   quality assessment, thematic synthesis, and gaps. This is the appropriate
   base for the current review.

The current article should use the systematic-evidence-map structure, but its
main Results hierarchy should be causal rather than omics-first:

1. Evidence landscape: populations/models, aging constructs, tissues, omics
   combinations, integration strategy, and study design.
2. Causal hypothesis/discovery studies.
3. Causal-effect evidence, subdivided by design family.
4. Validation and triangulation of the same causal link.
5. Recurrent aging mechanisms supported across designs.
6. Assumption, reporting, replication, and transportability gaps.

Omics layers should remain columns in the evidence tables and dimensions in
the evidence map. They should not define the primary narrative sections.

## Recommended article outputs

- **Figure 1:** final PRISMA flow.
- **Figure 2:** evidence landscape linking aging construct, biological system,
  omics combination, and causal design family.
- **Figure 3:** causal-link triangulation map showing discovery, effect
  evidence, and independent validation.
- **Table 1:** characteristics of all eligible studies.
- **Table 2:** causal hypothesis/discovery studies.
- **Table 3:** causal-effect studies with estimand, assumptions, diagnostics,
  and sensitivity analyses.
- **Table 4:** validation and replication of the same causal links.
- **Supplement:** database queries, complete extraction ledger, excluded
  reports and reasons, prompt versions, five-run stability, raw-response audit
  references, and human adjudications.
