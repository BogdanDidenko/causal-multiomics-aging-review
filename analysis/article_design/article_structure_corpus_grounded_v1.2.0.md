# Corpus-grounded article structure v1.2.0

## Status

This is the current working architecture for the review article. It supersedes
`article_structure_working_synthesis_v1.1.0.md` for article planning, but does
not change the registered scope, eligibility decisions, PRISMA counts, or the
Levels 0-4 rules.

It is grounded in four independent analyses of all 101 full-text-eligible
report profiles, with 35-40 deterministic full texts checked per analytical
question, followed by an independent synthesis. Docling Graph was used only to
locate candidate evidence and orient the corpus. Graph labels and exploratory
archetype counts are not final review findings.

The 101 records are eligible reports entering claim-level extraction. They are
not yet 101 independent studies or 101 final synthesis inclusions.

## Article identity

**Article type:** systematic review and evidence map with claim-level causal
appraisal.

**Recommended title:**

> How multi-omics studies test causal claims in biological aging: a systematic
> review and evidence map

**Central thesis:**

> Multi-omics studies of aging usually use molecular profiles to find or
> localize a candidate, while the causal claim depends on a perturbation,
> intervention, transfer, genetic instrument, or formal directed design. The
> evidence may be informative within a defined model and endpoint, but
> independent confirmation of the same link and transport to natural human
> aging require separate appraisal.

## Review questions

1. What aging phenomena, biological systems, and empirical workflows have been
   studied using multi-omics and a causal or formally directed design?
2. Where does causal leverage enter these workflows, and what claim is
   supported for the measured endpoint and system?
3. What does multi-omics add to the claim, and how independently and
   transportably has the same causal link been tested?

The detailed extraction fields answer these questions. They should not appear
as six or seven competing objectives in the Introduction.

## Organizing rule

Keep the public narrative simple and the audit model detailed:

- Results follow five questions a reader can understand.
- Causal level is assigned to a claim/link, not to a whole paper.
- Multi-omics has one dedicated Results section and one concise role field in
  the other sections.
- Validation is an overlay requiring same-link and independence judgments.
- Aging biology is organized by the phenomenon and endpoint measured, not by a
  generic Hallmarks catalogue.
- Levels 0-4 remain an implementation and appraisal device. They are not PRISMA
  categories and are not the main Results headings.

The repeated claim representation is:

`tested link | causal leverage | aging endpoint/system | omics contribution | level | independent same-link validation`

## Manuscript outline

### Structured abstract

- Background: multi-omics connects molecular layers but does not itself
  identify causal effects.
- Objective: map how aging claims are tested, what omics contributes, and how
  far the evidence is validated and transportable.
- Methods: systematic search, criterion-level screening, deterministic
  full-text processing, claim-level extraction, and design-specific appraisal.
- Results: report study, analysis, and link counts only after extraction.
- Conclusion: distinguish model-specific effects from evidence relevant to
  natural human aging.

### 1. Introduction

1. Biological aging is heterogeneous across time, biological scale, model, and
   endpoint.
2. Multi-omics can nominate, connect, and localize molecular components, but
   these functions differ from causal identification.
3. Existing reviews generally organize evidence by modality, biomarker,
   disease, or mechanism; they do not consistently ask what causal claim a
   workflow supports.
4. State the three review questions.

### 2. Methods

1. Protocol, reporting standards, amendments, and frozen search dates.
2. Eligibility criteria and Levels 0-4 definitions.
3. Search, deduplication, report linkage, retrieval, and unavailable reports.
4. Audited AI-assisted title/abstract and full-text screening, including five
   runs, deterministic packaging, grounding checks, retries, and human
   decisions.
5. Four linked units:
   `report -> study/cohort -> causal analysis -> normalized causal link`.
6. Claim-level extraction, including the causal contrast, system, endpoint,
   assumptions, diagnostics, result, and evidence span.
7. Multi-omics extraction, including assay scope, provenance, sample alignment,
   integration operator, timing, and the causal role of each layer.
8. Design-specific credibility, validation independence, and synthesis rules.

Methodological detail remains extensive because reproducibility is a strength
of the review. It does not determine the reader-facing Results hierarchy.

### 3. Results

Use exactly five subsections.

#### 3.1 What evidence base was found?

**Contains:** final PRISMA flow; reports, linked studies/cohorts, causal
analyses, and normalized links; publication formats; systems; aging phenomena;
natural versus induced models; and verified empirical workflow families.

**Question:** What kinds of studies and aging systems form the evidence base?

**Main display:** Figure 1, PRISMA plus the transition from reports to studies
and claims; Table 1, corpus characteristics with explicit denominators.

**Supplement:** complete ledgers, linkage decisions, unavailable reports, and
detailed species, tissue, aging-construct, and publication-format maps.

#### 3.2 Where did causal leverage enter the workflow?

**Contains:** two broad workflow families:

- experimental manipulation: target perturbation, assigned intervention, and
  transfer or host-ecosystem experiments;
- population and directed inference: genetic instruments, mediation, temporal
  or structural methods, and formal directed methods.

Within them, distinguish assignment, necessity, sufficiency, rescue/epistasis,
post-intervention molecular response, genetic-proxy effects, temporal/path
evidence, and computational prioritization.

**Question:** What was manipulated, assigned, instrumented, or formally
oriented, and what contrast did it support?

**Main display:** Figure 2, workflow from molecular profiling through causal
leverage to endpoint; Table 2, claim-level design and inferential boundary.

**Supplement:** the causal-analysis ledger, estimands, assumptions,
diagnostics, sensitivity checks, null findings, and proceedings-segmentation
audit.

#### 3.3 What did multi-omics contribute?

**Contains:** verified layer combinations and provenance; joint, sequential,
parallel, QTL/MR, and paired single-cell integration; and each layer's role as
candidate nominator, instrument source, exposure, mediator candidate, outcome,
localization, perturbation readout, or validation-only assay.

Explicitly separate cross-layer integration from multiple platforms within one
layer and from targeted confirmation.

**Question:** Did multi-omics contribute to identification, target nomination,
mechanistic localization, response measurement, or confirmation?

**Main display:** Figure 3, integration-architecture by causal-role matrix;
Table 3, definitions and representative verified workflows.

**Supplement:** all modality combinations, assay scope, integration operators,
sample alignment, data provenance, QTL semantics, and pairing status.

#### 3.4 What aspect of aging was affected?

**Contains:** findings grouped by measured object and endpoint depth:

1. organismal longevity, healthspan, and function;
2. natural tissue aging and loss of response capacity;
3. cellular or tissue senescence and age-related pathology;
4. intervention response and rejuvenation claims;
5. biological-age clocks and molecular proxies.

Every claim remains stratified by natural versus induced aging, biological
scale, species/system, and causal level. Reproductive aging, cancer-related
senescence, and plant/fruit senescence remain visible boundary strata.

**Question:** What aging outcome changed, in which system, and how deep was the
endpoint biologically?

**Main display:** Figure 4, aging phenomenon by endpoint depth and causal level;
Table 4, representative links ordered from survival/function to molecular
proxy.

**Supplement:** aging-measure dictionary, clock roles, reproductive-aging and
cancer-senescence panels, natural-versus-induced sensitivity analyses, and
species, tissue, and sex strata.

#### 3.5 How strong, independent, and transportable was the evidence?

**Contains:** final Levels 2-4; identification assumptions and diagnostics;
same-link replication; rescue and orthogonal perturbation; external predictive
validation kept separate; tissue, species, and model transport; human relevance;
and overextended interpretations.

**Question:** How far can a claim be trusted beyond the exact experiment in
which it was observed?

**Main display:** Figure 5, normalized-link validation and transportability
map; Table 5, design-specific credibility domains without a total score.

**Supplement:** complete level and validation ledgers, evidence quotations,
data-overlap matrix, appraisal judgments, human overrides, and PRISMA-trAIc
logs.

### 4. Discussion

1. Principal finding: where causal leverage came from and what role omics
   played.
2. What multi-omics adds beyond a single molecular layer.
3. The difference between model-specific effects and claims about natural
   human aging.
4. Recurrent biological response axes, considered only after causal appraisal.
5. Validation and transportability gaps.
6. Implications for study design and reporting.
7. Review strengths and limitations, including AI-assisted screening and the
   distinction between stability and validity.

### 5. Conclusion

Answer the three review questions without implying that multi-omics, pathway
convergence, a directed edge, a clock shift, or repeated model agreement
establishes causality by itself.

## Decisions relative to v1.1.0

Retained:

- claim-level classification and the four linked units;
- distinction between causal hypothesis and assessable causal effect;
- validation as a same-link, independence-aware overlay;
- design-specific credibility rather than a summed quality score;
- explicit separation of prediction, direction, identification, and
  validation.

Changed:

- formal causal discovery is no longer the first scientific Results stratum;
- `discovery -> effect -> validation` is an appraisal model, not the narrative
  sequence of the article;
- empirical workflows are collapsed into two reader-facing families;
- biological mechanisms move to the Discussion unless verified extraction
  supports a bounded endpoint-specific synthesis;
- omics modalities are not used as section headings;
- the title no longer overstates the formal causal-discovery subset.

## Freeze condition

Freeze this architecture only after claim-level extraction confirms that its
workflow and endpoint groups are usable across the corpus. Exact prevalence,
causal-level distributions, and biological conclusions must come from that
verified extraction, not from exploratory graph labels.

The reader-facing sequence is:

> What was found -> where causality entered -> what multi-omics added -> what
> aspect of aging changed -> how far the claim can travel.
