# Recommendation: adopt the WHO Content Model as the single primary methodology, with named amendments

## 1. Is the WHO Content Model the right single methodology?

Yes, with amendments. It is the only one of the five candidates whose native primitives cover all four of your stated requirements at once, rather than covering a subset and forcing the rest to be bolted on.

| Requirement | WHO primitive that satisfies it |
|---|---|
| Preserve one rich canonical graph | Foundation: multidimensional, poly-hierarchical, not mutually exclusive |
| Generate simple purpose-specific tables that may use exclusive categories | Linearizations: each one single-parent, mutually exclusive, exhaustive, auto-generated from the same Foundation |
| Handle variable study detail (arms, targets, estimators, directions) without new entities | Postcoordination: constrained axes and value sets on a base entity |
| Avoid overstating causality | Logical definitions vs necessary conditions (§3.8 to §3.10) |
| Boundary discipline across systems | Inclusions, exclusions, foundation-child-elsewhere |
| Codebook evolution and audit | Obsoletion status, backwards compatibility |

The honest test is whether a different single framework dominates it for a systematic review:

- **GO / GO-CAM** is the closest rival and is purpose-built for biological causal knowledge (Activity Units, typed causal edges, the NOT modifier, open-world assumption). But it is an annotation model. It does not natively produce the PRISMA flow, eligibility ledger, or evidence tables you are contractually obliged to deliver. Choosing it forces the entire reporting layer to be added on, which is exactly the multi-view job the WHO linearization mechanism already does. Its best ideas (explicit null records, open-world absence) fold into the WHO model as controlled axes rather than as a second framework.
- **Nickerson taxonomy development** is a method for building and validating a codebook, not a data model. It supplies the editorial discipline the WHO model assumes but does not specify. It is a governance procedure inside the chosen model, not a competing model.
- **SEI Views and Beyond** gives you the "multiple views plus first-class cross-view mapping plus recorded inconsistencies" idea, but with no controlled vocabulary, no compositional detail mechanism, and no definitional discipline. It is the views half of what WHO already provides.
- **W3C PROV-DM** is the audit backbone (entity, activity, agent, derivation), but it is domain-agnostic and models no scientific content and no counting units. It is a layer, not a primary methodology.

So the WHO Content Model is the maximal single choice. The reservation to state plainly: it is a classification-content architecture, not a causal-inference standard. It supplies machinery, not causal content and not entity-identity criteria. Those must be authored as domain axes and boundary rules. It also assumes a single reconciled authority, which conflicts with your two-extractor (Terra and Opus) design. Both gaps are addressable by amendment, which is why the decision is "adopt with amendments," not a clean "adopt."

## 2. Why this resolves the flat-analysis disagreement

The disagreement was never a data-quality problem. The agreement metrics show presence, design-family set, and causal-basis set agreeing 6/6, while the exact flat count agreed only 2/6. That pattern is the signature of an **undefined unit of count**, not of unreliable reading. The WHO model dissolves it in three moves.

1. **Counting becomes a property of a linearization, not of the corpus.** There is no global "number of causal analyses." Each Results question gets its own linearization with one declared counting unit (reports, studies, workflows, links, link-validation pairs). The Foundation stays many-to-many; each view is mutually exclusive and exhaustive by construction. A PRISMA report count and a causal-link count can never be confused because they live in different linearizations.

2. **Postcoordination absorbs the disputed dimensions.** Arms, targets, reverse directions, sensitivity estimators, rescues, and orthogonal assays were the exact features reviewers split on. In the WHO model these are axis values on a base entity, not new base entities. The entity-versus-axis boundary is decided once, in the Foundation specification, and then applied deterministically:
   - S1 Urolithin A: the nine-versus-twelve gap collapses because nested perturbations across one UA-centered mechanism are contrasts and validations on one workflow, not separate workflows.
   - S3 pear storage: high and low temperature are two contrast axis values on one intervention workflow, so five-versus-three collapses to one workflow plus targeted links.
   - S5 mtDNA: forward and reverse are two links (the instrument input changes identity), but IVW versus weighted-median are estimator axis values on one contrast, not new links, and the reverse null is a countable null link.

3. **Logical definition versus necessary condition stops validation from inflating counts.** A rescue, sensitivity check, or orthogonal assay is a Validation entity bearing a necessary-condition relation to its target link. It never enters the causal-link count. The Nickerson "mutually exclusive within a dimension" rule is expressed natively as the WHO linearization rule.

The net effect: the two things reviewers already agree on (presence, design-family set) become the primary reported numbers, and the thing they disagree on (a flat analysis count) is never reported as a single number. It is decomposed into workflow-count-by-family plus link-count plus contrast detail, each with a decided unit.

## 3. Minimal domain adaptation

Keep it small. Eight Foundation entity types, a short relation set, a fixed axis catalogue, explicit boundary rules, and seven generated views.

**Entity types (Foundation).** ReportVersion, Study, CausalWorkflow, CausalLink, Contrast, Validation, SourceEvidence, ExtractionAssertion. Resist adding more.

**Relations.** `describes` (ReportVersion to Study), `revisionOf` / `sameStudyAs` (version collapse), `contains` (Study to Workflow), `asserts` (Workflow to Link), `evaluatedBy` (Link to Contrast), `targets` (Validation to Link, Workflow, or Contrast), `supportedBy` (any object to SourceEvidence), `extractedFrom` and `adjudicates` (ExtractionAssertion).

**Controlled axes (postcoordination).**
- CausalLink: `causal_basis` {effect_identification_design, formal_directed_hypothesis}, `design_family` {nonrandomized_controlled_intervention, targeted_perturbation, genetic_instrument, mediation, ...}, `direction`, `exposure_type`, `outcome_construct`, `aging_phenomenon_stratum`, `assertion_polarity` {supported, null, challenged}.
- Contrast: `comparator`, `estimand`, `timepoint`, `arm`, `dose`, `subgroup`, `estimator`.
- Workflow: `omics_layers`, `integration_operator`, `layer_role`.
- Validation: `validation_type` {replication, rescue, orthogonal_assay, sensitivity, negative_control, challenge}, `result`, `independence`, `species_tissue_time_transfer`.
- ExtractionAssertion: `agent` {terra, opus, human_curator, script}, `activity` {screening, extraction, estimation_reading, source_check, adjudication}, `status` {extracted, adjudicated, superseded}.

**Boundary rules.**
- Individuation rule: create a new base entity only when an identity-defining input changes (different instrument, different outcome construct, different exposure). Otherwise it is an axis value. This single rule is what makes the count deterministic.
- Logical-definition gate: a CausalLink receives a necessary-and-sufficient logical definition only when exposure, outcome, direction, population, and estimand are all specified. Otherwise it carries necessary conditions only. Hypothesis-level links (S5 qualified directional hypothesis, S6 exploratory PIP greater than zero) never get logical definitions.
- Validation never counts as a Link or Workflow (exclusion).
- Non-molecular multimodal data (S6 accelerometry and MRI) sets an eligibility flag and a boundary reference to EC re-adjudication, rather than being silently admitted.
- Prediction and correlation-only reports (S4) are excluded from the causal-link linearization but retained in the evidence-base linearization with a status flag.

**Generated views (linearizations).** One per Results question, plus one operational audit view. See section 4 for counting units.

## 4. Object representation and what is countable

| Object | Foundation representation | Countable for |
|---|---|---|
| Report | ReportVersion: bibliographic and provenance, not a scientific unit | Q1 evidence base (report count, 376) |
| Study | Canonical investigation after version collapse | Q1 (study count, 357), Q4 |
| Workflow | Coherent causal procedure, the parent of related links; Activity-Unit-like | Q2 causal leverage (by design_family), Q3 multi-omics (by integration operator) |
| Link | One directed normalized biological claim, the synthesis unit | Q4 aging phenomenon, and the primary causal-link count |
| Contrast | The exact comparison and estimand bundle; axis values live here | never counted as a claim; qualifies a link |
| Validation | A targeted check with a target and a result | Q5 as part of link-validation pairs; never a link |
| SourceEvidence | A local locator atom (quote, table, figure, method) | audit only; supports every assertion |

**Counting map by Results question.**
- **Q1 evidence base:** count ReportVersions and canonical Studies separately, never conflated.
- **Q2 causal leverage:** count Workflows partitioned by `design_family`, reported as sets. This maps directly onto the 6/6 design-family agreement and replaces the unstable flat number.
- **Q3 multi-omics contribution:** count Workflows by integration operator and layer role.
- **Q4 aging phenomenon:** count Links or Studies by `aging_phenomenon_stratum`, keeping plant, fruit, clock, and disease-proxy strata distinct.
- **Q5 strength and transportability:** count Link-Validation pairs and polarity. The S5 reverse-MR null is a countable null link; the S6 failed univariate confirmation is a countable challenging validation.

The design principle: report what the reviewers agree on (presence Boolean, design-family set) as the headline numbers, and decompose what they dispute into workflow-by-family plus link count plus contrast detail.

## 5. Risks of misusing this methodology in a causal-evidence review

- **Treating an ontology edge as causal evidence.** The WHO model's own `associated with` axis (§4.13.1.15) explicitly does not specify the meaning of the relationship. If the adaptation borrows ICD `has causing condition` semantics loosely, you import diagnostic causality that is not statistical identification.
- **Propagating findings across boundaries via poly-hierarchy.** Do not let the S1 worm and cell UA mechanism inherit to human aging, and do not let plant and fruit senescence (S2, S3) be counted as mammalian aging through a shared "senescence" parent. GO's propagation caution applies directly.
- **Precoordination proliferation.** Minting a named precoordinated workflow entity for every combination reintroduces the exact count instability at the Foundation level. Default to postcoordination; precoordinate only genuinely recurrent patterns.
- **Single-authority collapse.** WHO assumes a reconciled Foundation. Forcing Terra and Opus into one Foundation prematurely destroys the competing-extraction signal, which here is scientifically informative.
- **False precision from logical definitions.** Assigning necessary-and-sufficient definitions to hypothesis-level links overstates identification.
- **Open-world violation.** No extracted record does not mean no analysis. Absent validation (S6 had no replication dataset) is "unknown," not "failed." Keep absent, unclear, and supported-null distinct.
- **Reading the linearization as the science.** A mutually exclusive table is a reporting artifact. Readers may mistake exclusivity for a biological fact. The Foundation is the truth-bearing layer; linearizations are lossy views.

## 6. Lean validation plan

Frame it as a demonstration of reproducibility and coverage, not as statistical validation. Claims stay modest.

1. **Counting reproducibility.** Apply the seven linearization counting rules to the disjoint six-report subset. Show that the two flat-count disagreements (S1 nine vs twelve, S3 five vs three) resolve to identical workflow-by-family counts once arms, targets, and estimators are axis values.
2. **Inter-rater reliability on decided units.** Re-extract a held-out sample of roughly 15 to 20 reports with two reviewers using the codebook. Report agreement separately on workflow individuation, link individuation, and axis values. Expectation: individuation agreement should now approach the presence and family agreement, because the entity-versus-axis boundary is pre-decided. Report Cohen or Krippendorff honestly, on decided units only.
3. **Coverage and termination (Nickerson objective conditions).** Confirm every active axis value has at least one supporting report, no in-scope object is unclassifiable, and no axis is duplicated.
4. **Boundary audit.** Confirm S4 is excluded from the causal-link linearization, S6 is flagged for EC re-adjudication, and both remain present in the evidence-base linearization.
5. **Provenance round-trip.** For a sample of adjudicated links, confirm traceability back to source locators and to both model drafts.

What not to claim: no claim that the taxonomy is uniquely correct (Nickerson explicitly denies uniqueness), no prevalence or statistical-validity claim from twelve purposive reports, and no claim that the model validates causal inference itself.

## 7. Production decision: adopt with named amendments

Adopt the WHO Content Model as the single primary methodology, subject to six amendments. The other four sources are subordinated, not co-equal: Nickerson becomes the codebook-authoring procedure, GO-CAM and V&B and PROV contribute specific content decisions and axes inside the WHO model.

- **A1. Preserve competing extractions.** The Foundation stores the adjudicated entity plus links to superseded ExtractionAssertions. This corrects the single-authority assumption while keeping one model.
- **A2. Add `assertion_polarity` and explicit absent/unclear handling.** Encodes the GO NOT modifier and open-world discipline so nulls and challenges are first-class and absence is never read as negative.
- **A3. Fold provenance into the audit linearization** as controlled agent, activity, and derivation axes, rather than importing PROV-DM as a second formalism. This keeps a single methodology.
- **A4. Author the individuation rule and the logical-definition gate as mandatory Foundation content** before any counting occurs. These are the two rules that make counts deterministic and prevent overstated causality.
- **A5. Record known cross-view inconsistencies as data** (the V&B contribution), because unreconciled reviewer disagreement is scientifically informative in this review.
- **A6. Restrict precoordination to recurrent workflow patterns;** default to postcoordination.

Do not alter the frozen eligibility ledger, the PRISMA flow, or the accepted five-question structure. The entity model sits underneath them and feeds them; it does not replace them.
