# Corpus-grounded manuscript structure for the causal multi-omics aging review

## Purpose and evidential boundary

This report proposes an article structure from four independent exploratory audits of the 101 full-text-eligible reports and from the comparator-review analyses. It is an article-design document, not a new eligibility or evidence-classification analysis.

The Luna Light graph labels and the exploratory archetype counts are orientation aids. They are not accepted as review findings. Any number used in the final manuscript must come from the frozen claim-level extraction after report-to-study linkage and full-text verification. Nothing proposed here changes PRISMA counts, eligibility decisions, or Levels 0-4.

## Core conclusion

The earlier structure was too complicated because it tried to make several valid analytical dimensions compete as the main narrative: causal design, aging biology, omics modality, discovery versus effect, and validation. The corpus suggests a simpler division of labor:

1. **The reader-facing story follows what the studies actually did.** Studies profiled aging systems and then used a perturbation, assigned intervention, biological transfer, genetic instrument, or formal directed method to test or orient a claim.
2. **Multi-omics has one dedicated analytical role.** It shows how molecular layers nominated, localized, connected, or validated that claim; it is not itself evidence of causality.
3. **Causal strength is a claim-level appraisal applied throughout.** Levels 0-4, assumptions, diagnostics, validation independence, and transportability do not become competing article sections or paper-level labels.
4. **Aging biology is synthesized by the aging phenomenon and endpoint actually measured.** It is not forced into a generic Hallmarks-style mechanism catalogue.

## Agreements among the four corpus reports

### 1. The report is not the correct unit for causal judgment

All four audits show that one publication can contain omics discovery, computational prioritization, an intervention or perturbation, downstream molecular responses, and a rescue experiment. These steps support different claims. The article must therefore retain the linked units:

`report -> study/cohort -> causal analysis -> normalized causal link`

Descriptive corpus characteristics can be report-level. Causal appraisal and validation must be claim/link-level.

### 2. Formal causal discovery is not the dominant empirical behavior

The archetype and causal-design audits agree that controlled perturbations and interventions are much more prominent than formal DAG, SCM, Bayesian-network, mediation, or causal-discovery workflows. The old `discovery -> effect -> validation` sequence is therefore not a faithful primary account of the corpus.

That sequence remains useful as an appraisal concept: a claim may remain hypothesis-level, support an assessable contrast, or have independent same-link validation. It should not imply that most reports proceed through three sequential study phases.

### 3. Multi-omics usually scaffolds the causal workflow

The integration and causal-design audits converge on the same distinction:

- causal leverage usually comes from assignment, perturbation, transfer, an instrument, or an assumption-dependent directed design;
- omics usually nominates a target, localizes a response, proposes a mediator, broadens measurement, or provides triangulation;
- parallel molecular changes, pathway concordance, or extra assays do not independently strengthen identification;
- targeted qPCR, western blotting, immunostaining, or a similar validation assay must not automatically be counted as another discovery-scale omics layer.

### 4. Validation is an overlay, not a third study type

The reports agree that the word “validation” covers very different operations: a rescue in the same system, an orthogonal assay, another tissue, another species, a reused public cohort, or an independent test of the same normalized link. These cannot be combined into one yes/no paper label.

The article should ask two questions for each validation claim:

1. Does it test the same exposure-to-outcome link?
2. Is the evidence materially independent of the discovery and identification evidence?

### 5. The measured aging object must remain visible

The biological-aging and causal-design audits agree that lifespan, healthspan, tissue function, pathology, cellular senescence, an omics signature, and a biological-age clock are not interchangeable endpoints. Natural aging, induced senescence, premature-aging models, age-related disease, cancer-cell senescence, reproductive aging, and plant/fruit senescence also have different biological meanings and transportability.

### 6. Mechanistic coherence should be interpreted late

Metabolism, inflammatory or senescent niches, systemic or microbial transfer, and chromatin regulation recur across the corpus. All four audits nevertheless caution against making these pathway labels the primary Results hierarchy. The same pathway name can describe association, post-intervention response, or perturbational necessity in different systems.

## Tensions and their resolution

| Tension | Why it arises | Resolution in the manuscript |
|---|---|---|
| Empirical archetypes versus causal design families | Archetypes describe whole-report workflows; design families classify individual claims. | Use a small number of empirical workflows to tell the story. Apply design family and causal level to each extracted claim within those workflows. |
| Methods-first versus biology-first organization | Causal strength is central to the review, but readers need to know what kind of aging was studied. | Present causal workflows first, then synthesize findings by measured aging endpoint. Keep the causal appraisal visible in both. |
| A dedicated multi-omics section versus integrating omics everywhere | Omics role is central but a modality catalogue would fragment the story. | Use one compact Results subsection on integration architecture and role; repeat only a short omics-role field in other tables. |
| Six exploratory archetypes versus six claim-level causal categories | Two six-part taxonomies would be difficult to follow and would appear redundant. | Collapse report archetypes into two reader-facing families: experimental manipulation and population/directed inference. Keep the six causal categories in the extraction codebook and supplement, not as six Results headings. |
| Discovery/effect/validation as narrative versus as appraisal | It is too abstract to represent common report workflows but remains useful for Levels 2-4. | Remove it from the article spine. Retain hypothesis/effect level and validation as columns in every claim-level synthesis. |
| Broad mechanism synthesis versus heterogeneous aging constructs | A pathway-first synthesis risks treating clocks, cellular senescence, disease, and lifespan as equivalent. | Organize biological results by aging phenomenon and endpoint depth. Discuss recurrent response axes only after those boundaries are shown. |

## Plain-language narrative thesis

> Multi-omics studies of aging usually use molecular profiles to find or localize a candidate, while the causal claim depends on a separate perturbation, intervention, transfer, genetic instrument, or directed design. The evidence is often informative within a specific model and endpoint, but independent confirmation of the same causal link and transport to natural human aging remain the key limitations.

This thesis is specific enough to be testable after claim-level extraction and simple enough to carry the entire article.

## Recommended title

### Replace the current working title

Current title:

> Causal discovery and causal-effect evidence in multi-omics studies of biological aging: a systematic review and evidence map

Recommended title:

> **How multi-omics studies test causal claims in biological aging: a systematic review and evidence map**

Reason: “causal discovery” in the current title gives disproportionate prominence to a small formal-method subset. “Test causal claims” covers perturbations, interventions, transfers, genetic instruments, and formal directed hypotheses without implying that all claims are identified or validated.

Conservative alternative:

> **Causal evidence in multi-omics studies of biological aging: a systematic review and evidence map**

## Revised review questions

Replace the six parallel questions with three primary questions. The detailed fields remain in the extraction codebook rather than the Introduction.

1. **What aging phenomena, biological systems, and empirical workflows have been studied using multi-omics and a causal or formally directed design?**
2. **Where does causal leverage enter these workflows, and what claim is supported for the measured endpoint and system?**
3. **What does multi-omics add to the claim, and how independently and transportably has the same causal link been tested?**

These questions preserve the protocol scope and Levels 0-4 while giving the reader one sequence: field -> claim -> credibility.

## Full manuscript outline

### Structured abstract

- **Background:** multi-omics can connect molecular layers but does not itself identify causal effects in aging.
- **Objective:** map how causal claims are tested, what omics contributes, and how far the evidence is validated and transportable.
- **Methods:** systematic search, criterion-level selection, audited AI-assisted screening, deterministic full-text processing, claim-level extraction, design-specific appraisal, and narrative evidence mapping.
- **Results:** report final study and claim counts only after extraction; summarize empirical workflows, omics integration roles, aging endpoints, causal levels, and independent same-link validation.
- **Conclusion:** distinguish evidence within a defined experimental system from evidence that supports natural human aging or intervention claims.

### 1. Introduction

#### 1.1 Why causal questions in aging are difficult

Define the heterogeneity of aging by scale and endpoint: cellular state, tissue function, disease, biological-age proxy, healthspan, and lifespan. Explain the special problems of time, model origin, and transportability.

#### 1.2 What multi-omics can and cannot add

Explain target nomination, cross-layer localization, mediation hypotheses, response profiling, and triangulation. State explicitly that additional layers do not replace identification assumptions or experimental control.

#### 1.3 The review gap

Existing reviews organize aging research by omics technology, biomarkers, disease area, or biological mechanism. The unresolved question is what causal claim each workflow actually tests and how the omics layers contribute to that test.

#### 1.4 Objective and review questions

Present the three questions above. Avoid introducing all extraction axes in the Introduction.

### 2. Methods

The Methods should remain detailed because reproducibility is a contribution of this review. Their detail should not dictate the reader-facing Results hierarchy.

#### 2.1 Protocol, reporting standards, and amendments

Report registration, PRISMA/PRISMA-S and PRISMA-trAIc use, protocol versions, search dates, and all amendments. Keep superseded pilots and legacy graph-assisted runs outside the final denominator but available in the audit trail.

#### 2.2 Eligibility criteria

Define empirical report, aging relevance, at least two analytically connected molecular omics layers, and the accepted causal or formally directed design boundary. Preserve EC1-EC5 and Levels 0-4 unchanged.

#### 2.3 Search, deduplication, report linkage, and retrieval

Provide database-native queries, branch counts, export dates, hashes, DOI/title deduplication, linked-report handling, full-text retrieval sources, and unavailable reports.

#### 2.4 AI-assisted title/abstract and full-text screening

Describe the frozen prompts/templates, model and reasoning configuration, five independent runs, deterministic packaging, quotation grounding, retry rules, unanimous-exclusion routing, manual decisions, stability results, and retained raw outputs. State that reproducibility is not validity.

#### 2.5 Units and claim-level extraction

Use the four linked units. For each causal analysis extract the population/model, exposure or intervention, comparator, outcome, time, estimand or directed-hypothesis meaning, design family, assumptions, diagnostics, result, and evidence span.

For each molecular layer extract modality, assay scope, source, sample alignment, integration operator, timing, and causal role. Distinguish discovery-scale omics, genetically proxied molecular traits, and validation-only assays.

For aging extract phenomenon, natural versus induced model, biological scale, endpoint depth, clock role, tissue, species, and sex where relevant.

#### 2.6 Evidence classification and validation

Apply Levels 0-4 at the causal-analysis/link level using the frozen Python rules. Treat validation separately through same-link match, independence, model/tissue/species relation, and whether the validation supports identification, mechanism, prediction, or only measurement.

#### 2.7 Design-specific credibility appraisal

Use conditional domains for assigned interventions, direct perturbations, transfers, genetic instruments, mediation, temporal designs, structural/directed models, and causal-discovery algorithms. Do not calculate one cross-design quality score.

#### 2.8 Synthesis

Describe report-to-study linkage, handling of shared cohorts and public datasets, denominator rules, qualitative grouping, and why heterogeneous effects are not pooled indiscriminately. State that the exploratory graph audits informed article design only; all manuscript findings derive from verified full-text extraction.

### 3. Results

Use exactly five subsections.

#### 3.1 What evidence base was found?

**Contains:** the final PRISMA flow; counts of reports, linked studies/cohorts, causal analyses, and normalized links; publication formats; model systems; aging phenomena; natural versus induced models; and a compact map of the dominant empirical workflows. Exploratory six-archetype assignments must be replaced by verified extraction before reporting prevalence.

**Question answered:** What kinds of studies and aging systems make up the evidence base?

**Main displays:** Figure 1, PRISMA flow plus the transition from reports to studies and claims; Table 1, corpus characteristics with an explicit denominator column.

**Supplement:** complete report ledger, report-linkage decisions, excluded and unavailable reports, detailed species/tissue/aging maps, publication-format audit, and all descriptive counts.

#### 3.2 Where did causal leverage enter the workflow?

**Contains:** two broad workflow families rather than six competing sections:

- **Experimental manipulation:** target-first perturbation, treatment/intervention, and transfer or host-ecosystem experiments.
- **Population and directed inference:** genetic instruments, formal mediation/temporal/directed methods, and map/clock workflows that progress to a formal test.

Within both families, identify the strongest tested link and distinguish assigned exposure, necessity, sufficiency, rescue/epistasis, post-intervention molecular response, genetic-proxy effect, temporal/path evidence, and computational prioritization. Associational steps inside otherwise eligible papers remain visible but are not promoted to causal effects.

**Question answered:** What was actually manipulated, assigned, instrumented, or formally oriented, and what contrast did that design support?

**Main displays:** Figure 2, a workflow map from molecular profiling through the source of causal leverage to the measured endpoint; Table 2, claim-level design and inferential-boundary summary.

**Supplement:** complete causal-analysis ledger; estimands; design-specific assumptions, diagnostics, and sensitivity checks; claim chains; proceedings-segmentation audit; null and conflicting findings.

#### 3.3 What did multi-omics contribute?

**Contains:** verified layer combinations and provenance; joint, sequential, parallel, cross-dataset QTL/MR, and paired single-cell integration; the role of each layer as candidate nominator, instrument source, exposure, mediator candidate, outcome, localization, perturbation readout, or validation-only assay. Explicitly separate genuine cross-layer integration from multiple assays within one layer and from targeted confirmation.

**Question answered:** Did multiple omics layers change identification, nominate the tested target, localize the response, propose a mechanism, or only broaden/confirm measurement?

**Main displays:** Figure 3, an integration-architecture-by-causal-role matrix or alluvial plot; Table 3, definitions and representative verified workflows.

**Supplement:** full layer and modality combinations, assay scope, integration operators, sample alignment, data provenance, QTL semantics, single-cell pairing status, and single-omics sensitivity analyses.

#### 3.4 What aspect of aging was affected?

**Contains:** findings grouped by the measured aging object and endpoint depth:

1. organismal longevity, healthspan, and function;
2. natural tissue aging and loss of response capacity;
3. cellular/tissue senescence and age-related pathology;
4. intervention response and rejuvenation claims;
5. biological-age clocks and molecular proxies.

Every result remains stratified by natural versus induced aging, biological scale, species/system, and causal level. Reproductive aging, cancer-related senescence, and plant/fruit senescence are visible boundary strata, not silently merged with organismal human aging.

**Question answered:** What aging outcome changed, in which system, and how biologically deep was that endpoint?

**Main displays:** Figure 4, an evidence map crossing aging phenomenon with endpoint depth and causal level; Table 4, representative normalized links ordered from survival/function to molecular proxy.

**Supplement:** complete biological-aging measure dictionary; clock roles and training targets; reproductive-aging panel; cancer-senescence panel; natural-versus-induced and kingdom/species sensitivity maps; sex- and tissue-specific results.

#### 3.5 How strong, independent, and transportable was the evidence?

**Contains:** the distribution of Levels 2-4 after final extraction; identification assumptions and diagnostics; independent same-link replication; rescue and orthogonal perturbation; external predictive validation kept separate; tissue/species/model transport; human relevance; and unsupported or overextended claims. The section reports claim-level credibility, not a paper score.

**Question answered:** How far can each causal claim be trusted beyond the exact experiment in which it was observed?

**Main displays:** Figure 5, normalized-link validation and transportability map; Table 5, design-specific credibility domains with `n/N` and no total score.

**Supplement:** complete level ledger, validation-independence audit, source-to-target map, data-overlap matrix, all appraisal judgments and evidence quotations, human overrides, and PRISMA-trAIc screening logs.

### 4. Discussion

#### 4.1 Principal finding

Return to the narrative thesis: omics generally scaffolds causal workflows, while causal leverage comes from a more specific design. State the final balance of workflow and evidence types only from verified extraction.

#### 4.2 What multi-omics adds to causal aging research

Discuss nomination, localization, cross-layer mechanism generation, response coverage, and triangulation. Contrast these contributions with actual identification.

#### 4.3 From model-specific effects to aging claims

Discuss endpoint depth, natural versus induced aging, necessity versus sufficiency, biomarker reversal versus functional rejuvenation, and differences between cell, model-organism, and human claims.

#### 4.4 Recurrent biological response axes

Only here synthesize adaptive metabolism/energetics, senescent niche and inflammatory communication, systemic or microbial transfer, and chromatin regulation when supported by verified claims. Treat them as cross-cutting interpretations, not equivalent causal pathways.

#### 4.5 Validation and transportability gaps

Discuss independent same-link replication, data reuse, tissue and ancestry mismatch, sex specificity, intervention specificity, clock circularity, and the scarcity or strength of human functional outcomes.

#### 4.6 Implications for future study design and reporting

Recommend explicit estimands, prospective validation targets, assay provenance and sample alignment, intervention-on-mediator tests, independent replication, functional endpoints alongside molecular clocks, and transparent separation of prediction from causation.

#### 4.7 Strengths and limitations

Cover search terminology, unavailable full texts, report and dataset dependence, heterogeneous designs, limited pooling, publication bias, AI-assisted screening, graph-audit limitations, and the distinction between screening stability and scientific validity.

### 5. Conclusion

Answer the three review questions in one short paragraph. Do not conclude that multi-omics, pathway convergence, a directed edge, an aging-clock shift, or repeated model agreement establishes causality by itself.

## How causal appraisal fits without complicating the story

The article should use one repeated claim card or table row throughout Results:

`tested link | source of causal leverage | aging endpoint/system | omics contribution | Level 2-4 | independent same-link validation`

This single representation replaces several parallel taxonomies in the main text. The six detailed causal categories, all assumptions, and all diagnostics remain necessary, but they live in the extraction codebook, detailed tables, and supplement. In prose, each claim uses precise verbs such as “changed,” “was required for,” “was sufficient for,” “was genetically proxied to affect,” “preceded,” or “was prioritized.”

## How multi-omics integration fits without complicating the story

Multi-omics receives one main Results subsection because it is part of the review question. Elsewhere, it is represented by one concise field: its role in the causal workflow. The article should not repeat layer catalogues in each biological section.

The central distinction is:

> **The causal design determines why a contrast may be interpreted causally; multi-omics determines which molecular components were connected, selected, localized, or measured.**

This wording allows strong joint integration, sequential discovery-to-perturbation, parallel response profiling, QTL/MR integration, and validation-only assays to coexist without implying equal inferential value.

## Main-text versus supplement rule

The main article should contain the scientific argument and denominator-based summaries. The supplement should contain the complete audit trail and high-dimensional classifications. A practical rule is:

- **Main text:** one question, one denominator, and one interpretive message per display.
- **Supplement:** every record, claim, quote, assumption, diagnostic, override, and alternative classification needed to reproduce that message.

## Final recommendation

Freeze the manuscript architecture only after the claim-level extraction verifies the prevalence of the proposed workflow families and aging endpoint groups. The five Results subsections above are stable even if the exploratory counts change because they follow the actual logic of the studies rather than the graph labels.

The simplest reader-facing sequence is:

> **What was found -> where causality entered -> what multi-omics added -> what aspect of aging changed -> how far the claim can travel.**
