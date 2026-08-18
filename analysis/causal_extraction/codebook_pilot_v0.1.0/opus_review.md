# Claude Opus 5 independent codebook review

## Runtime provenance

- Date: 2026-08-18
- CLI selector: --model opus --effort high
- Canonical review model: claude-opus-5
- Auxiliary CLI model: claude-haiku-4-5
- Permission mode: plan; Edit and Write disabled
- Status: success
- Turns: 69
- Wall duration: 1,599,645 ms
- API duration: 1,516,852 ms
- Session ID: 22baaf9f-a78a-4d28-955c-9f47c3fb893b
- Review result length: 51,683 characters
- Role: advisory independent model review, not expert gold labeling

## Verbatim review
Write is disabled in this session, so the review is delivered here in full rather than written to a file. Nothing in the repository was modified.

---

# Independent methodological review: claim-level causal identification instrument v0.1.0

Reviewer role: independent senior causal-inference methodologist. Read-only throughout.

## 1. Runtime review scope and limitations

**Read in full or substantial part**

- `protocol/causal_extraction/v0.1.0/codebook.md` (366 lines, complete)
- `protocol/causal_extraction/v0.1.0/claim_record.schema.json` (286 lines, complete)
- `analysis/causal_extraction/codebook_pilot_v0.1.0/README.md`, `reports_15.csv`, `self_audit.md` (complete)
- `claims.jsonl`: all 20 records, every field
- `scripts/validate_causal_codebook_pilot.py` (complete)
- All 15 deterministic Docling sources (~1.25 MB). For each report I read the Methods, Results and Discussion/Limitations passages bearing on every coded field, not only the quoted spans.

**Programmatic checks run (read-only)**

- Re-implemented the deterministic level mapping independently: 0 mismatches against `candidate_level`.
- Verified all 47 quotes are exact substrings of the cited file: 47/47 pass.
- Compared each anchor's `section_heading` against the file's actual headings and against the nearest preceding heading to the quote.
- Scanned all 15 sources for paywall/preview markers and for presence of Results/Methods/Discussion/Limitations.
- Tabulated field distributions, assumption-domain vocabulary, omics-layer vocabulary, quote lengths, validation dimensions.
- Tested a candidate derivation for `qualifies_for_level4` against the 5 recorded validations.

**Limitations**

1. This is a single model reviewer. It measures agreement between one advisory reviewer and one primary analyst. It is not inter-rater reliability, not a kappa estimate, and must not be reported as expert gold validation.
2. Supplementary files and figures are outside the deterministic corpus. Where a coded field depends on a supplementary figure (the CASP8 siRNA null in Suppl. Fig. 8-9, the female-fly curves in Fig. S4), I could verify only the main-text description.
3. Docling loses some heading structure (the FSHW "2.4 Lifespan assay" heading is absorbed into "2.3 Heat Stress Assay"). Where a heading mismatch is a conversion artefact rather than an analyst error, I say so.
4. I did not exhaustively enumerate every causal statement in the 15 reports. My segmentation findings name specific omitted claims with exact quotes; they are a lower bound.
5. I did not re-run the validator (it imports `jsonschema` and would write bytecode). I re-implemented its substantive checks inline; my results reproduce its reported PASS on every check it performs.
6. Two files declared in the pilot README (`opus_review.md`, `cross_audit.md`) do not exist, so no prior adjudication was available.

## 2. Overall verdict

**REVISE** for continued instrument development. Not production. Not ready for a larger human-coded pilot without the section 6 fixes.

The four-field separation of author claim, design provenance, identification assessability and result direction is well conceived and it demonstrably worked: I reach the same value as the analyst on 75% of claims across all seven non-segmentation decision fields, and the instrument correctly resisted six author overclaims a naive extractor would have accepted. But the deterministic validator certifies exactly the properties that do not bear on scientific validity and is silent on the four that do: whether the cited source is adequate, whether a quote supports the field it is attached to, whether the decisive fields are anchored at all, and whether claim boundaries are reproducible. The pilot contains one Level-3 claim coded from a paywalled abstract-only source, one polarity-inverted evidence quote, an unenforced Level-4 gate, and a segmentation rule the pilot itself violates in three places.

## 3. Per-claim audit (all 20 claims)

**A** = agree, **D** = disagree with replacement value, **A\*** = agree on the value but a correction is proposed elsewhere in the record. "Seg" = segmentation. "L4" = Level-4 validation status.

| # | claim_id | Seg | author_claim_type | primary_design | source_of_var | reviewer_assessment | result_status | level | L4 | Source-backed reason |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | jamapsych_2024_smoking_longevity_mr | **D** | A | A | A | A | A | A | A | Uncoded null MVMR for a distinct exposure set: "the adverse impact of major depression, problematic alcohol use, and drinks per week on longevity attenuated with MVMR, suggesting that the genetic liabilities of these exposures had no direct associations with longevity". Also a distinct EAA outcome. Separately the estimand attributes β −0.33 to MVMR (abstract) while Results attributes the identical numbers to SVMR: "SVMR estimates showed negative associations between longevity and the genetic liability for major depression, lifetime smoking (longevity β, −0.33; 95% CI, −0.38 to −0.28". |
| 2 | imo2_2026_uterus_weight_mediation | A | A\* | A\* | A\* | A | A | A | A | `temporal ordering` should be `violated` not `unclear`: the mediator is a carcass trait measured at slaughter after the outcome window closed. "We analyzed a cohort of 254 Rhode Island Red laying hens at 100 weeks of age." plus "the number of eggs produced from 85 to 100 weeks (EN85-100". Drop `genetic_instrument` from supporting methods: SMR was applied to expression→UW100, not to this link. Author type is borderline because the report self-labels the analysis statistical: "The mediation framework used in this study provides a statistical decomposition of genetic effects into indirect and direct components." |
| 3 | cels_2021_stabilized_regression_edges | A | A | A\* | A\* | A | A | A | A | Correct call: "estimates whether the selected target is more likely to be upstream of a canonical pathway (i.e., causal), downstream (i.e., a biomarker), or ambiguous". The enum has no value for invariance/environment-based methods, so `causal_discovery_algorithm` is a forced fit; and because diet was investigator-assigned ("Diets were either Harlan Teklad 2018 (CD"), a second reviewer could code `quasi_exogenous_rule_or_event`. The `metabolomics: mechanistic_localization` role is unsupported for an analysis run on 3,772 mRNA/protein products. |
| 4 | cels_2021_asp4_lifespan_perturbation | **D** | A | A | A | A | A | A | A\* | Two uncoded claims meet every split criterion: st-7 RNAi ("st-7 inhibition with RNAi caused a minor reduction in lifespan of around 11%", "st-7 inhibition halved lifespan") and asp-4 × daf-2 epistasis ("in the RB2035 background, this effect was much reduced"). Validation `data_independence: independent` for a same-lab replicate should be `partially_independent`; the codebook excludes "Internal robustness". Good catch that the operation is the ok2693 mutant, not the "knockdown" the paper's own summary calls it. |
| 5 | natcom_2023_twas_focus_prioritization | **D** | **D** → `association_prediction_or_prioritization` | A | **D** → `inherited_genetic_variation` | **D** → `no_identification` | A | **D** → `1` | A | The normalized claim's verb is "prioritize", output is `candidate_prioritization`, and the codebook maps "prioritizing only" to `no_identification` and puts "candidate ranking" under prioritization. FOCUS ranks within a locus: "A PIP > 0.5 indicates that the feature is the most likely causal feature within a risk region". `formal_hypothesis_only` requires a directed/mediation/temporal/structural/discovery method; Bayesian fine-mapping is none. Provenance is genotype-derived predicted expression. Uncoded: the drug-target MR, this pilot's only real test of the MR-versus-drug boundary ("genes that could be targeted pharmacologically"), and the immune-trait MR. |
| 6 | natcom_2023_metabolite_longevity_mr | **D** | A | A | A | A | A | A | A | Assumption text verified in Methods ("we used MR-Lasso ... to remove outlier variants", "the MR Steiger test of directionality showed strong evidence"), but the same section holds an uncoded null: "we failed to identify any significant effects of circulating metabolites on EAA." Only 2 of 9 genetic-instrument domains recorded; sample overlap unaddressed although both GWAS draw on UK Biobank. |
| 7 | npjaging_2026_dq_kidney_aging | **D** | A | A | A | A | A | A | A | Randomization fully supported: "Allocation to experimental groups was performed by random number tables, and investigators were kept blinded to group assignments". Analyst correctly refused the "systemic rejuvenation" framing via "the present work does not directly establish improvement in renal function". But one claim bundles five endpoint families against a unit definition of "one outcome", and the module-required multiplicity domain is absent despite dozens of endpoints under one-way ANOVA without cross-family correction. |
| 8 | nataging_2023_parabiosis_lifespan | **D** | A | A | A\* | A | A | A | **D** | Lifespan coding accurate (log-rank P = 0.001 is in the Fig. 1c legend). Two problems. The epigenetic-age outcome is a distinct claim under the split rules but was demoted into `validations`. And `compositional specificity: violated` merges two module domains and mis-assesses one: the report did control physical attachment. "To isolate the effects of blood sharing and physical attachment, we performed mock parabiosis". |
| 9 | nataging_2026_hotairm1_crispri_senescence | **D** | A | A | A | **D** → `unclear` | **D** → `unclear` | **D** → `manual_review` | A | **Most serious finding.** The cited source is a paywalled preview: "This is a preview of subscription content, [access via your institution]". No Results, Methods, Discussion or Limitations section exists in it. `effect_assessable` requires "an inspectable identification strategy"; the codebook defines `unclear` as "The supplied full text is insufficient for classification". Two of three anchors are abstract sentences. `exposure_operation` also merges CRISPRi, siRNA and AAV overexpression, violating "different exposure operations even when they share a gene symbol" and inconsistent with claims 17/18. `hota_a2` is labelled "Supplementary Table 15" but sits under Supplementary Table 2. `population_or_model` omits WI-38, the system used for the siRNA senescence assay. |
| 10 | stackage_2026_lifestyle_aging_mediation | A | A | A\* | A | A | A | A | A | Correct and well anchored: "the cross-sectional design of the proteomic and metabolomic measurements precludes the direct assessment of intra-individual aging dynamics"; cohort verified ("30 376 participants were retained"). `sem` here versus `mediation_analysis` in claims 2/11 for the same claim shape is an undefined boundary, and the actual mediator is the fitted aging-rate index, not the proteins coded `mediator_candidate`. |
| 11 | pesa_2023_inflammation_mediation | A | A | A | A | A | A | A | **D** | Assessment right, disclaimer faithfully quoted ("the nature of this study does not allow to establish a causal effect between SA and EAA"). But `sequential ignorability: not_reported` is wrong: the assumption is explicitly invoked and defended. "under the sequential ignorability assumption. This supposition is plausible considering the design of the omics cohort, with cases and controls matched based on gender and age." And the report proposes an external validation ("Publicly available methylomics and transcriptomics data from the Multi-Ethnic Study of Atherosclerosis (MESA) were used as external validation") absent from an empty array. |
| 12 | agingcell_2025_aged_fmt_cognition | **D** | A | A | A\* | A | **D** → `mixed_or_time_specific` | A | A | The flagship recognition-memory endpoint was not significant in recipients: "significantly reduced in aged donors, while showing a declined trend in young recipients". Separately the contrast is confounded by an unnamed asymmetric pretreatment: "For recipients, mice were first treated with an antibiotics cocktail" versus "Young control mice and old donor mice were gavaged with sterile PBS daily at the same time." The reviewer_note says component interventions are needed when the report performs exactly those (sections 2.5-2.7, including an AHR-antagonist design), all uncoded. |
| 13 | agingcell_2025_tpe_epigenetic_clocks | A | A | A | A | A | A | A | A | I agree on the disputed TPE allocation, and this is the instrument's best moment. Contrast is inspectable and FDR-corrected against sham, so `effect_assessable` is right, while allocation is `violated` on "Randomization was carried out based on the first-come first-served principle" and "The shorter duration testing groups ... were filled, followed by longer duration testing groups". `mixed_or_time_specific` exact: "we observed no significant BA differences at time point 3 compared to sham in any group". Two additions required: anchor the contradicting "Enrolled patients were randomly allocated to four groups (in a 1:1:1:1 scheme)", and add multiplicity (36 clocks; "we used nominal p values to identify increasing and decreasing trends"). |
| 14 | agingcell_2026_losartan_dose_metabolome | **D** | A | A | A | A | A | A(cond.) | A | The source is stronger than the record shows: the fitted model has no time term, so dose absorbs it. "AgingSignature ~1 + Dose + I (Dose^2) + (1\|ID)" alongside "it is impossible to separate potential effects of drug dose alone from total time on drug". "U"-shaped is exactly sourced. But Level 2 rests entirely on the undefined `formal_basis_present = yes`, the only record where it is consulted; and the report's primary claims are uncoded, including "we did find a statistically significant improvement in survival of geriatric mice treated for a short duration with losartan". |
| 15 | msystems_2025_iaa_lifespan | A | A | A | A | A | A | A | A | Accurate, including the 50 µM figure ("IAA supplementation (50 µM) extended the lifespan by approximately 15% (about 10 days)"), replication ("n = 5 biological duplicates, 40-45 male flies for each duplicate") and a matched vehicle ("finally added to the medium at a concentration of 0.25% DMSO"). One correction: `population_or_model` says "male and female" but the deterministic source's lifespan curves are male only. |
| 16 | msystems_2025_iaa_ahr_sirt2_epistasis | **D** | A | A | A | A | A | A | A | Same merging violation as claim 9: Ahr mutant, Sirt2 mutant and Sirt2 RNAi are three operations across two genes in one claim, while the same pilot split the CASP8 operations. The record is commendably transparent that the contrast is a difference in significance, which is what the source reports: "both flies with knockdown and mutant of Sirt2 exhibited no significant changes in the lifespan compared with their corresponding controls". No genotype × treatment interaction test, and mutants have different baselines ("Ahr mutant Drosophila ... exhibited a marked decrease in lifespan"), so an `interaction_estimand` domain is required. |
| 17 | cellcommsig_2026_casp8_inhibitor_senescence | **D** | A | A | A\* | A | A | A | A | Best-executed claim. Normalizing to the compound rather than to caspase-8 is exactly right, and the off-target assessment is precisely sourced: "revealed significant reduction of activity of all three caspases with all concentrations and under all time points". The report reaches the analyst's conclusion itself: "we consider that the observed effects of Z-IETD-FMK are more appropriately interpreted as modulation of TNF-α-associated inflammatory and chondrocyte phenotypes, rather than as direct evidence that the inhibitor reverses TNF-α-induced caspase-8 activation." One recoding: "Vehicle controls ... were included" is unsupported; Methods document "Untreated cells (without TNF-α or Z-IETD-FMK) served as baseline controls". Uncoded: the non-OA null for the same exposure and outcome ("no significant changes were observed in cell viability, proliferation or SA-β-Gal across all treatment groups ( p > 0.05)") and the CASP8 MR claim. |
| 18 | cellcommsig_2026_casp8_sirna_senescence | A | A | A | A | A | A | A | A | Correctly split from claim 17, and retaining a null at Level 3 is right. But anchor `casp_si_a2` is a 30-character fragment, "the same  biological  question", excerpted from "genetic deletion and catalytic-site inhibition do not address exactly the same biological question". Read alone it asserts the opposite of the source. A `functional_target_engagement` domain is also required: only 85% mRNA knockdown is shown, and the report documents mRNA/protein–activity decoupling in this system ("increased CASP8 mRNA and intracellular protein expression but did not significantly alter caspase-8 enzymatic activity"), which is decisive for a null. |
| 19 | fshw_2026_cordycepin_lifespan | **D** | A | A | A | A | A(cond.) | A | A | Values verified against Table 1. But the record cites the whole dose series to support `dose and matched control: addressed` while scoping the claim to the favourable subrange, when the same series contains a significant harm (10 mg/mL, 13.12 d, −37.61%, P < 0.0001) and the paper calls the response "Non-monotonic". Also the `dose specification` anchor points to an efficacy figure; the supporting text is "plate concentration cannot be directly translated into internal exposure metrics". The DAF-16 epistasis, which the reviewer_note itself calls "a separate claim", is uncoded although the source states "cordycepin-mediated lifespan extension requires DAF-16 activity". |
| 20 | fshw_2026_cordycepin_daf2_target | A | A | A | A | A | A | A | A | Correct Level 1, well anchored. One recoding: `normalized_claim` asserts "IGF-1R/DAF-2 is a direct upstream molecular target of cordycepin", which the report explicitly declines to claim: "with IGF-1R/DAF-2 emerging as a computationally prioritized candidate" and "direct upstream target engagement remains to be established". Grading a disclaimed claim as `no_identification` is circular. |

## 4. Agreement counts

| Decision-driving field | Agree | Disagree | Agreement | Disagreeing claims |
|---|---:|---:|---:|---|
| Claim segmentation | 8 | 12 | 40% | 1, 4, 5, 6, 7, 8, 9, 12, 14, 16, 17, 19 |
| `author_claim_type` | 19 | 1 | 95% | 5 |
| `primary_design_or_method` | 20 | 0 | 100% | — |
| `source_of_identifying_variation` | 19 | 1 | 95% | 5 |
| `reviewer_identification_assessment` | 18 | 2 | 90% | 5, 9 |
| `result_status` | 18 | 2 | 90% | 9, 12 |
| `candidate_level` | 18 | 2 | 90% | 5, 9 |
| Level-4 status (negative determination) | 20 | 0 | 100% | — |
| Level-4 status (array completeness) | 18 | 2 | 90% | 8, 11 |

**Exact all-field agreement (all eight fields including segmentation): 7/20 = 35%** — claims 2, 3, 10, 13, 15, 18, 20.
**Exact agreement on the seven non-segmentation fields: 15/20 = 75%** — disagreeing: 5, 8, 9, 11, 12.

Essentially all loss is concentrated in segmentation and two boundary cases. The taxonomy is close to usable; the unit of annotation is not.

Ancillary measurements:

- Deterministic level mapping: 20/20 reproduce.
- Quote substring grounding: 47/47 pass.
- `section_heading` verifiability: 16/47 anchors name a heading matching nothing in the cited file; 9/47 name a string absent from the file entirely.
- Quote length: 7/47 under 60 characters; 3 are bare noun phrases; 1 inverts the source's polarity.
- Assumption coverage: 41 judgments across 20 claims (median 2) against modules specifying 6-9 domains each — roughly 22-33% coverage. 38 distinct free-text `domain` strings for 41 judgments.
- `diagnostics`: empty in 18/20.
- `validations`: empty in 15/20; 5 records total; `qualifies_for_level4` is `no` in 5/5, so the Level-4 branch has never fired.
- `formal_basis_present`: `yes` in 19/20; functionally consulted in exactly 1 record.
- `omics_roles.layer_or_modality`: 21 distinct strings for 45 entries, two of them not omics layers.

## 5. Codebook and schema findings by severity

### Fatal (block a larger human-coded pilot)

**F1. Source adequacy is never checked, and one report is a paywalled preview.** `10.1038/s43587-026-01100-7` contains "This is a preview of subscription content" and has no Results, Methods, Discussion or Limitations. It produced a Level-3 `effect_assessable` claim with `contrast_complete = yes`. Scanning the other 14 sources found no further paywall markers, so it is isolated, but it is undetectable by the validator and it is the difference between Level 3 and manual review.

**F2. The Level-4 gate is unconstrained.** `expected_level` reads `any(item["qualifies_for_level4"] == "yes")` and nothing else. A reviewer may set `yes` on a validation with `same_link_alignment = none` and `data_independence = not_independent` and both schema and validator will assign Level 4. Fixable at zero cost: a derivation over the four already-recorded dimensions reproduces all 5 analyst judgments exactly (5/5).

**F3. The evidence contract is unenforced for the fields that set the level.** The schema attaches `evidence_anchor_ids` only to `assumption_judgments`, `diagnostics` and `validations`. `author_claim_type`, `primary_design_or_method`, `source_of_identifying_variation`, `reviewer_identification_assessment`, `result_status`, `estimand_or_contrast` and `contrast_complete` carry none. The schema therefore contradicts the codebook's own rule that "Every decisive field requires ... a shortest exact quotation". Every numeric estimand I checked was genuinely sourced, to the analyst's credit, but none is anchored.

**F4. Substring grounding admits misleading and polarity-inverted quotes.** `casp_si_a2` passes validation while asserting the opposite of its source. Two further anchors are non-probative noun phrases ("results of colocalization analyses"; "corroborated smoking-longevity associations", the latter attached to two assumption domains it supports neither of). This is the clearest demonstration that technical grounding is not scientific support.

**F5. Segmentation is not reproducible, and the pilot violates its own rule.** 12/20 claims need boundary changes. The operation-splitting rule was applied in the CASP8 report and violated in two others in the same pilot (claims 9 and 16). `conflicting_within_report` is structurally unreachable at 0/20: if conflicting operations are always split, no claim can carry the value, yet the CASP8 report is the paradigm conflict. The ledger holds one null while I located at least three uncoded ones with exact quotes. Acceptance question 5 cannot be answered from this pilot.

**F6. Design-specific assumption modules are prose, not contract.** The schema permits `assumption_judgments: []`; in practice every claim carries exactly two entries against modules of 6-9 domains. `domain` is a free string, producing 38 distinct values for 41 judgments, so assumption coverage cannot be aggregated. Two coders will not converge on which two of nine domains to record. Self-audit item 7 identifies this; I confirm it is fatal rather than cosmetic.

**F7. `formal_basis_present` is undefined and decides Level 1 versus 2.** It is the sole discriminator in "`effect_claim_not_assessable` with a formal directed/design basis → 2", and "formal basis" is never defined. `yes` in 19/20, consulted in exactly one record, where flipping it changes the level.

### Major

**M1. The codebook contradicts itself on `inherited_genetic_variation`.** The enum row says "Valid genetic instrument in MR/IV analysis"; the paragraph below says the field "describes provenance of the contrast, not its validity". This contradiction is what pushed claim 5 to `observational_covariation`.

**M2. One `source_of_identifying_variation` cannot express assignment and exposure material at once.** Randomized parabiosis, non-randomized FMT and non-randomly allocated TPE are among the corpus's most important distinctions; the field renders the first two identical and pushes the third into a value silent about the material. Only free-text `reviewer_note` carries it, defeating the stated purpose.

**M3. No rule says which node of a multi-node claim fixes the source of variation.** Mediation claims can have inherited exposure and observational mediator (claim 2); directed-edge claims can have assigned environments and observational edges (claim 3); TWAS has genotype instruments and imputed exposure (claim 5). All three were coded by unstated convention.

**M4. `contrast_complete` is a validity proxy, not its stated checklist.** Three of four `no` codings satisfy all six sub-items as written; `no` is signalling "not a valid causal contrast". Self-audit item 3 anticipates this.

**M5. `addressed` is undefined between "reported" and "adequately handled".** Used both ways, with claim 11 showing the cost. `violated` is also misused there for an author disclaimer, which is a category error, on an invented domain duplicating `reviewer_identification_assessment`.

**M6. `method_output_type` has no rule for loss- and gain-of-function designs.** Four comparable claims received three values: germline null → `total_effect` (4), CRISPRi → `necessity` (9), siRNA → `necessity` (18), pharmacologic inhibition → `total_effect` (17). Transfer designs the authors call "sufficient" ("gut microbiota from naturally aged mice is sufficient to induce declined cognitive behaviors") are `total_effect`. The codebook insists these must not be collapsed but gives no application rule.

**M7. `omics_roles.layer_or_modality` is free text and admits non-omics evidence.** 21 strings for 45 entries; the same layer appears as "methylomics" and "DNA methylation/epigenomics", as "16S microbiome profiling", "microbiome profiling" and "metagenomics/16S"; two entries are not omics at all ("worm survival assay", "network pharmacology databases"). For a multi-omics review the layer count is a headline result and it is not reproducible. No role exists for "input to a derived composite index", which is what claim 10's proteomics actually is.

**M8. An empty `validations` array is ambiguous** between "none proposed" and "proposed and rejected". 15/20 are empty, and claim 11 shows the failure: MESA is proposed by the report and absent from the record. Level 4 gates entirely on this array.

**M9. `section_heading` is unverifiable free text.** 16/47 match no heading; 9/47 name a string absent entirely. Some are innocent Docling artefacts. Others materially mislabel: four CASP8 anchors label Results as "Functional assays"; `hota_a2` cites the wrong supplementary table; `iaa_epi_a2` labels a figure-legend region "Discussion"; `stack_a2` cites "Limitations" in a paper with no such heading. Section provenance is decision-relevant given the codebook's own rule that abstracts do not override Results, Methods or Limitations.

**M10. Level 1 versus 2 has no rule for prioritization claims.** Claims 5 and 20 share design, output type and `contrast_complete` yet land on 2 and 1. A defensible distinction exists (claim 5 has a genotype-derived contrast) but is unstated.

**M11. `diagnostics` is a dead field overlapping `assumption_judgments`** (empty in 18/20). Two overlapping free-text arrays double the divergence surface for no analytic gain.

**M12. The README describes work not in the repository.** It lists `opus_review.md` and `cross_audit.md`, and Procedure steps 4-5 describe a completed model review and analyst adjudication. Neither file exists; this review is step 4. A reader would conclude the adjudication had occurred.

### Clarifications (worth fixing, not blocking)

- **C1.** No rule for `author_claim_type` when authors use a causal method name and explicitly disclaim causal interpretation (hen: "provides a statistical decomposition"; PESA: "does not allow to establish a causal effect").
- **C2.** `quasi_exogenous_rule_or_event` versus `investigator_assigned_exposure` for administrative allocation rules. "Plausibly exogenous" is the discriminator and is not operationalized; first-come-first-served is literally a rule.
- **C3.** No endpoint-bundling rule. Claim 7 bundles five families; claims 17/18 split finely.
- **C4.** `rescue_or_epistasis` collapses two logical operations. Endorse self-audit item 1.
- **C5.** Null perturbations as `causal_effect` is correct but implicit. Endorse self-audit item 4; state it.
- **C6.** `sem` versus `mediation_analysis` for the same claim shape (claims 2, 10, 11).
- **C7.** The design enum lacks an invariance/environment-based value, forcing claim 3 into `causal_discovery_algorithm`.
- **C8.** `candidate_level` is stored although fully derivable; storing an annotated copy invites drift.
- **C9.** `omics_role: validation_only` and `assay_scope: validation_only` encode the same fact twice.
- **C10.** No field captures "the report's stated interpretation of its own result", which would have cleanly held the CASP8 and FSHW self-corrections.

## 6. Minimal proposed v0.2.0 changes

Design principle: no new ontology. Each change deletes discretion, converts an existing judgment into a derivation over fields already collected, or adds one sentence of definition.

### 6.1 Schema edits

**S1. Anchor the decisive fields.** Add a required `field_anchors` object:

```json
"field_anchors": {
  "type": "object", "additionalProperties": false,
  "required": ["author_claim_type","primary_design_or_method",
               "source_of_identifying_variation","reviewer_identification_assessment",
               "result_status","estimand_or_contrast","contrast_complete"],
  "patternProperties": {"^[a-z_]+$": {"type":"array","minItems":1,"items":{"type":"string"}}}
}
```

**S2. Derive `qualifies_for_level4`.** Remove it from the record. Compute it:

> `qualifies_for_level4 = yes` if and only if `same_link_alignment == "exact"` **and** `data_independence == "independent"` **and** `experimental_independence == "independent"` **and** `purpose == "identification"` **and** `result_status == "supports_claim"`. Otherwise `no`. If any input is `unclear`, the value is `unclear` and the claim routes to manual review rather than Level 4.

Verified: reproduces all 5 analyst judgments in the pilot, 5/5.

**S3. Make `assumption_judgment.domain` an enum keyed to the design module**, taken verbatim from the codebook's existing module lists so no new concepts are introduced: `allocation_mechanism`, `comparator_integrity`, `adherence_and_contamination`, `attrition_and_analysis_population`, `baseline_balance`, `assigned_contrast_analysis`, `outcome_timing_and_multiplicity`, `manipulated_operation_and_target`, `matched_control`, `intervention_specificity_or_off_target`, `functional_target_engagement`, `timing_relative_to_outcome`, `replication`, `necessity_sufficiency_or_rescue_logic`, `outcome_relevance_to_aging`, `donor_and_recipient_definition`, `transfer_procedure_and_control`, `recipient_assignment`, `compositional_specificity`, `co_transferred_material_and_interference`, `transfer_timing_and_outcome`, `instrument_relevance_and_strength`, `independence_and_ld_handling`, `exclusion_restriction_and_pleiotropy`, `directionality`, `population_and_sample_overlap`, `ancestry_and_tissue_relevance`, `heterogeneity_and_robust_estimators`, `colocalization`, `exposure_precedes_mediator_and_outcome`, `exposure_outcome_exchangeability`, `exposure_mediator_exchangeability`, `mediator_outcome_exchangeability`, `no_exposure_induced_confounder`, `interaction_handling`, `direct_and_indirect_estimands`, `sensitivity_analysis`, `temporal_spacing_and_lag`, `stationarity`, `time_varying_confounding`, `acyclicity_and_faithfulness`, `causal_sufficiency`, `markov_equivalence`, `edge_orientation_basis`, `interventional_or_instrumental_anchors`, `stability_and_external_checks`, `interaction_estimand`.

**S4. Split assignment from exposure material.** Keep `source_of_identifying_variation`, add one required orthogonal field:

```json
"assignment_mechanism": {"enum": ["randomized","investigator_assigned_nonrandom",
  "quasi_exogenous_rule_or_event","unassigned_observational","inherited","none","unclear"]}
```

Claim 8 becomes `transferred_biological_material` + `randomized`; claim 12 `transferred_biological_material` + `investigator_assigned_nonrandom`; claim 13 `investigator_assigned_exposure` + `investigator_assigned_nonrandom`.

**S5. Close the omics vocabulary.**

```json
"layer_or_modality": {"enum": ["genomics","epigenomics_dna_methylation",
  "chromatin_accessibility","transcriptomics_bulk","transcriptomics_single_cell",
  "transcriptomics_spatial","proteomics","metabolomics","lipidomics","glycomics",
  "microbiome_amplicon","microbiome_metagenomic","immunophenotyping_cytomics","other_omics"]}
```

Add required sibling `molecular_qtl_layer` (`enum: ["eqtl","pqtl","mqtl","sqtl","none"]`) so "transcriptomics/eQTL" need not be smuggled into a layer name. Add role value `composite_index_input`.

**S6. Add a required `source_adequacy` block.**

```json
"source_adequacy": {"type":"object","additionalProperties":false,
  "required":["full_text_status","sections_available"],
  "properties":{
    "full_text_status":{"enum":["full_text","abstract_or_preview_only",
                                "proceedings_abstract","partial","unclear"]},
    "sections_available":{"type":"array","items":{"enum":["abstract","introduction",
      "methods","results","discussion","limitations","figure_legends","supplementary_captions"]}}}}
```

**S7. Disambiguate empty validations.** Add required `"validations_proposed_by_report": {"enum": ["none","one_or_more","unclear"]}`, with `one_or_more` requiring at least one entry.

**S8. Drop `diagnostics`**, folding content into `assumption_judgments` under S3.

**S9. Remove `formal_basis_present` and `candidate_level` from the record**; both become derivations.

### 6.2 Definition edits (exact wording)

**D1. Fix the `inherited_genetic_variation` contradiction.**

> `inherited_genetic_variation` — The exposure contrast is generated by germline genotype, including Mendelian randomization, instrumental-variable analysis, transcriptome-wide association with genotype-derived expression weights, and summary-data-based MR. Code this value whenever germline genotype generates the contrast, regardless of whether the relevance, independence or exclusion-restriction assumptions are adequately addressed. Instrument validity is recorded in `assumption_judgments` and in `reviewer_identification_assessment`, never here.

**D2. Add the multi-node provenance rule.**

> When the annotated claim spans more than two nodes, code the source of variation for the single link named in `normalized_claim` that carries the claimed effect. For a mediated claim this is the mediator-to-outcome link, because that link carries the indirect effect. For a directed-edge or structure claim between two measured variables this is the variation in the pair of measured variables, not the variation in the design's environment, instrument or grouping variables. Record the other links' provenance in `reviewer_note`.

**D3. Define, then derive, the Level 1 versus Level 2 boundary.** Delete `formal_basis_present` as an annotated field; replace the two mapping rows with:

> `effect_claim_not_assessable` maps to Level 2 when `primary_design_or_method` is one of `randomized_intervention`, `controlled_nonrandomized_intervention`, `quasi_experiment`, `targeted_genetic_perturbation`, `targeted_pharmacologic_perturbation`, `biological_transfer`, `genetic_instrument`, `mediation_analysis`, `temporal_model`, `dag_scm`, `sem`, `bayesian_network`, `causal_discovery_algorithm`, `invariance_or_environment_based_model` or `other_formal_design`. It maps to Level 1 when `primary_design_or_method` is `predictive_or_associational_model`, `computational_prioritization`, `none` or `unclear`.

Claim 14 then stays Level 2 by a stated criterion rather than by discretion.

**D4. Resolve prioritization claims explicitly.**

> `formal_hypothesis_only` requires a method whose output is a direction, a mediated path, a temporal ordering, a structural relation, or a discovered edge. Within-locus or within-network ranking methods, including fine-mapping posterior inclusion probabilities, colocalization posteriors, network centrality and docking scores, produce a ranking rather than a direction and are coded `no_identification` even when the method's name or the authors' wording contains the word causal.

This resolves claim 5 to Level 1 and preserves claim 20 at Level 1, removing the unexplained split.

**D5. Define `addressed`.**

> `addressed` means the report explicitly reports an analysis, a design feature, or a stated argument bearing on this assumption. It does not mean the assumption holds or that the handling is adequate; that judgment belongs in `assessment` and, where decisive, in `reviewer_identification_assessment`. `violated` is reserved for assumptions the source shows to be violated as a matter of fact. An author's statement that the study cannot establish causality is not an assumption violation; record it in `reviewer_note` and reflect it in `reviewer_identification_assessment`.

**D6. Define the necessity / sufficiency / total-effect boundary.**

> For a loss-of-function operation whose outcome is a phenotype the exposure is claimed to be required for, code `necessity`. For a gain-of-function or transfer operation whose outcome the exposure is claimed to be able to induce, code `sufficiency`. Code `total_effect` only when the claim is the magnitude or direction of a contrast between two conditions without a necessity or sufficiency assertion, for example a survival difference between genotypes reported as a lifespan effect. When the source asserts requirement or sufficiency in words, prefer `necessity` or `sufficiency` over `total_effect`.

**D7. Split `rescue_or_epistasis`** into `rescue` and `effect_modification_or_epistasis` (self-audit item 1). Claim 16 becomes `effect_modification_or_epistasis`.

**D8. State the null-perturbation and endpoint-bundling rules.** In `author_claim_type`:

> A claim whose tested contrast is causal is coded `causal_effect` even when the observed estimate is null; result direction is recorded only in `result_status`.

In "Unit of annotation":

> Bundle several endpoints into one claim only when the source reports them as a single pre-specified composite, or when they are measured on one assay platform and reported through one contrast with one multiplicity correction. Otherwise split by endpoint family. When the same exposure operation and outcome yield different result directions in different populations, systems or dose ranges, split by that stratum and code each stratum's `result_status` separately; use `conflicting_within_report` only for a single normalized link whose own evidence is internally contradictory.

Add to "Prohibited shortcuts": *Do not annotate a claim the report explicitly declines to make; normalize the claim to what the source asserts.*

### 6.3 Validator additions

**V1.** Derive and assert `candidate_level`, `formal_basis_present` (as a derived intermediate per D3) and `qualifies_for_level4` (per S2) rather than comparing an annotated copy.

**V2.** Reject any quote shorter than 60 characters unless it is a complete sentence, and reject quotes beginning or ending mid-clause. Operational proxy: require at least six whitespace-separated tokens and sentence-boundary or block-boundary termination on both sides. This alone catches `casp_si_a2`, `nat_twas_a1` and `mr_a2`.

**V3.** Enforce module completeness: given `primary_design_or_method`, require the corresponding module's domains to be present, each with a status and at least one anchor. Any may be `not_reported`; none may be silently absent.

**V4.** Flag source adequacy: detect paywall/preview markers and absent Methods/Results content per cited file, require `source_adequacy.full_text_status` to be consistent, and where it is not `full_text` forbid `reviewer_identification_assessment` values other than `unclear` absent an explicit override note.

**V5.** Verify `section_heading` mechanically: require it to equal the nearest preceding Markdown heading to the quote. Move the paper's own section name to an optional free-text `section_label`.

Also assert that every file declared in the pilot README exists.

## 7. Claims that should be recoded, with replacement values

### Changing a decision-driving field

**Claim 9** `nataging_2026_hotairm1_crispri_senescence`
- `reviewer_identification_assessment`: `effect_assessable` → **`unclear`**
- `result_status`: `supports_claim` → **`unclear`**
- `candidate_level`: `3` → **`manual_review`**
- `contrast_complete`: `yes` → **`unclear`**
- `source_adequacy.full_text_status`: **`abstract_or_preview_only`**
- Reason: "This is a preview of subscription content, [access via your institution]". No Results, Methods, Discussion or Limitations in the cited file.
- Also: split into three claims by operation; relabel `hota_a2` to Supplementary Table 2; add WI-38 to `population_or_model`.

**Claim 5** `natcom_2023_twas_focus_prioritization`
- `author_claim_type` → **`association_prediction_or_prioritization`**
- `source_of_identifying_variation` → **`inherited_genetic_variation`**
- `reviewer_identification_assessment` → **`no_identification`**
- `candidate_level` → **`1`**
- Reason: "A PIP > 0.5 indicates that the feature is the most likely causal feature within a risk region"; the normalized claim's verb is "prioritize"; "Non-colocalized gene-trait associations cannot be interpreted as causal relationships."

**Claim 12** `agingcell_2025_aged_fmt_cognition`
- `result_status` → **`mixed_or_time_specific`**. Reason: "significantly reduced in aged donors, while showing a declined trend in young recipients".
- `comparator` → "young control mice receiving sterile PBS without antibiotic pretreatment"; add `transfer_procedure_and_control` = **`violated`**, anchored to "For recipients, mice were first treated with an antibiotics cocktail" and "Young control mice and old donor mice were gavaged with sterile PBS daily at the same time."; correct the reviewer_note.

### Within assumption records, validations and free text

**Claim 1**: estimand → "SVMR beta −0.33 (95% CI −0.38 to −0.28) per Results; the abstract attributes the same estimate to MVMR, and no MVMR point estimate appears in the main text". Re-anchor both assumption domains to the sensitivity-analysis sentences.

**Claim 2**: `exposure_precedes_mediator_and_outcome` `unclear` → **`violated`**. Drop `genetic_instrument` from supporting methods.

**Claim 3**: drop the `metabolomics: mechanistic_localization` role.

**Claim 4**: validation `data_independence` → **`partially_independent`**. Remove "worm survival assay" from `omics_roles`. Add the st-7 and asp-4 × daf-2 claims.

**Claim 6**: add `population_and_sample_overlap` = **`not_reported`** and `colocalization` = **`not_applicable`**; add the metabolite-on-EAA null as a separate claim with `result_status = null`.

**Claim 7**: add `outcome_timing_and_multiplicity` = **`not_reported`**; split the five endpoint families.

**Claim 8**: split into `compositional_specificity` = **`violated`** and `co_transferred_material_and_interference` = **`addressed`**, the latter anchored to "To isolate the effects of blood sharing and physical attachment, we performed mock parabiosis". Promote the epigenetic-age outcome out of `validations` into its own claim.

**Claim 11**: `sequential ignorability` → **`addressed`**, anchored to "under the sequential ignorability assumption. This supposition is plausible considering the design of the omics cohort, with cases and controls matched based on gender and age." Delete the `causal effect identification = violated` entry. Add a MESA validation entry with `same_link_alignment = none`, `purpose = identification`, non-qualifying, and set `validations_proposed_by_report = one_or_more`.

**Claim 13**: add a second anchor, "Enrolled patients were randomly allocated to four groups (in a 1:1:1:1 scheme)", under `allocation_mechanism`. Add `outcome_timing_and_multiplicity` = **`violated`**, anchored to "we used nominal p values to identify increasing and decreasing trends".

**Claim 14**: `contrast_complete` `no` → **`yes`** under the six-item rule as written, with invalidity carried by `reviewer_identification_assessment`. Re-anchor `dose-time separability` to "AgingSignature ~1 + Dose + I (Dose^2) + (1|ID)". Add the mouse survival, mouse metabolome and cardiac proteome claims.

**Claim 15**: `population_or_model` → "male w1118 flies, 40-45 per replicate, n = 5 replicates; female results reported only in supplementary figures outside the deterministic corpus".

**Claim 16**: split into three claims by operation and gene; `method_output_type` → **`effect_modification_or_epistasis`**; add `interaction_estimand` = **`not_reported`**.

**Claim 17**: split into `functional_target_engagement` = **`addressed`** and `matched_control` = **`unclear`**, the latter anchored to "Untreated cells (without TNF-α or Z-IETD-FMK) served as baseline controls". Add the non-OA null and the CASP8 MR claim.

**Claim 18**: replace `casp_si_a2` with the full sentence "This might be because genetic deletion and catalytic-site inhibition do not address exactly the same biological question." Add `functional_target_engagement` = **`not_reported`**, anchored to "increased CASP8 mRNA and intracellular protein expression but did not significantly alter caspase-8 enzymatic activity".

**Claim 19**: either widen to the full dose range with `result_status` = **`mixed_or_time_specific`**, or add a separate claim for the 10 mg/mL harm (13.12 ± 4.75 d, −37.61%, P < 0.0001) and narrow the `dose and matched control` assessment. Re-anchor `dose specification` to "plate concentration cannot be directly translated into internal exposure metrics". Add the DAF-16 epistasis claim.

**Claim 20**: `normalized_claim` → "Network pharmacology and molecular docking prioritize IGF-1R/DAF-2 as a candidate upstream target of cordycepin in C. elegans", anchored to "with IGF-1R/DAF-2 emerging as a computationally prioritized candidate" and "direct upstream target engagement remains to be established".

## 8. Answers to the six self-audit questions

1. **Are the four core fields mutually distinguishable in all 20 records?** Yes, and this is the strongest result. `author_claim_type` diverged from `reviewer_identification_assessment` in 8 of 20 records without either collapsing, and I agree with the analyst 19/20 and 18/20 respectively.
2. **Should observational mediation always be `formal_hypothesis_only`?** Not as a blanket rule, but no claim here earns better. All three fail a source-verifiable prerequisite: mediator measured after the outcome window (2), cross-sectional mediator by the authors' own statement (10), explicit causal denial (11). Keep it as default and require `effect_assessable` to be justified by recorded, non-`not_reported` statuses on all four exchangeability domains plus a sensitivity analysis. Do not make the authors' disclaimer the criterion, which is what self-audit item 5's heuristic effectively does.
3. **Is the TPE contrast correctly classified as assessable?** Yes. I independently reach `effect_assessable` with `controlled_nonrandomized_intervention` and `investigator_assigned_exposure`. The between-group comparison against sham is real and FDR-corrected across 36 clocks, while allocation and baseline-balance violations correctly stay in the assumption record instead of being smuggled into the level. Two additions required: the contradicting 4.3 sentence, and multiplicity.
4. **Does any validation satisfy Level 4?** No, and my proposed derivation reaches the same verdict on all five without discretion. But this is a null result about the sample, not evidence that the rule discriminates: the positive branch has never fired, and the current gate would accept a Level 4 asserted on a `related_mechanism`, `not_independent` validation.
5. **Does the MR coding distinguish a genetically proxied effect from a drug or behavioural intervention?** In the two coded MR claims, yes and cleanly. But the pilot avoided the cases where the boundary bites: the Nat Commun drug-target MR ("To model potential effects of pharmacologically targeting our MR-identified genes") and the CASP8 MR, which carries the overclaim "The SMR/HEIDI results further exclude linkage confounding, demonstrating that the associations reflect a true causal effect of CASP8 itself". The prohibited shortcut is correctly written and untested.
6. **Which fields can be deterministic derivations?** `candidate_level` (already), `formal_basis_present` (from `primary_design_or_method`, per D3), `qualifies_for_level4` (verified 5/5), and the minimum required assumption domains (per V3). `contrast_complete` can be derived if decomposed into its six stated sub-items as booleans; as a single judgment it will keep drifting toward `effect_assessable`.

## 9. Final go / no-go for a larger independent human-coded pilot

**No-go as currently specified. Go after a bounded v0.2.0 revision, and only with the unit of annotation fixed first.**

The taxonomy is nearly ready and the four-field architecture should be kept essentially as is: my independent recoding agrees on 75% of claims across all seven non-segmentation fields and on 90-100% of each field individually. But sending two human coders at this instrument today would measure segmentation variance, not the taxonomy: I proposed boundary changes on 12 of 20 claims, and the pilot applies its own operation-splitting rule inconsistently across three reports. Any kappa from that would be uninterpretable, and a poor number would be blamed on the categories rather than on the unit.

1. **Fix the unit first, then re-code the same 15 reports.** Write the claim-enumeration protocol self-audit item 6 calls for, apply D8 and the operation-splitting rule mechanically, and re-code these 15 reports to convergence. Expect roughly 35-45 claims rather than 20. Single-analyst, cheap, and a precondition for any reliability measurement.
2. **Ship the fatal fixes** F1-F7 as v0.2.0. All are small and mechanically verifiable.
3. **Then run the two-coder pilot** on 25-30 reports drawn to include what this sample lacks: at least three plausible Level-4 candidates so the positive branch is exercised, at least three reports whose primary claim is null, at least two proceedings abstracts or otherwise partial sources so the adequacy gate is exercised, and at least two reports that conflate an MR estimate with a drug effect. Pre-register targets by field and report segmentation agreement separately from field agreement; pooling them hides exactly what this review found.
4. **Do not treat this review as validation.** It is one advisory model reviewer; the README's language on that point is correct and should survive unchanged. The validator's PASS should likewise be described as what it is: 20 records that are schema-valid, quote-grounded and mapping-consistent, three properties that are necessary and, as claim 9 shows, jointly insufficient.

One closing note in the instrument's favour. The pilot caught six author overclaims a name-matching extractor would have accepted: "systemic rejuvenation" without renal function, "Randomization" that was first-come-first-served, a "U-shaped dose response" fully confounded with time, a caspase-8 attribution the compound cannot support, a docking-based "direct target", and a parabiosis effect correctly narrowed to no single circulating factor. That is the instrument doing precisely the job the codebook sets for it. The problems above concern enforcement and the unit of annotation, not the concept.


