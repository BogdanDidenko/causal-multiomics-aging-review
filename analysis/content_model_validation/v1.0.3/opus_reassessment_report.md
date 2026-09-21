# Reassessment: WHO Content Model after the CMACM v1.0.3 reproducibility failure

Short version: this result does not weaken the choice of WHO. It confirms the one reservation the prior report stated explicitly ("it supplies machinery, not causal content and not entity-identity criteria"). The failure landed exactly where WHO delegates to the domain, and the domain wrote that delegation loosely. Below are direct answers to all five questions, plus the one procedural change that matters more than any of them.

## 1. Does this weaken WHO, or show the adaptation misused postcoordination?

It shows the adaptation misused postcoordination and linearization. WHO cannot be falsified by a reproducibility failure at the individuation boundary, because WHO contains no individuation criteria. It provides three mechanisms (Foundation, postcoordination axes, mutually exclusive linearizations) and one rule (Foundation identity is decided per domain). Amendment A4 in the prior report was supposed to author that identity rule as mandatory Foundation content before counting. It was authored, but with two hollow phrases: "identity-defining input" for workflows and "outcome construct changed" for links. Three model runs filled those blanks three different ways. That is under-authoring, not a wrong framework.

One candid addition the prior report understated: even a perfectly authored identity rule will not produce three-run agreement if you ask a language model to apply it as a judgment. The 8/15, 5/15, 10/15 pattern is a model-discretion signature layered on top of the under-specification. The fix is therefore two parts, a precise identity spec (below) and a procedure that removes the model's discretion over counting (question 5).

## 2. Minimal individuation specification

The governing principle: the model never decides a count. It emits typed atoms with attribute values drawn from closed vocabularies, and code derives every countable object by hashing an identity key. An entity's identity key is the exhaustive list of inputs that split it; nothing else can.

**`CausalWorkflow`. Foundation entity. Countable (Q2, Q3).**
Identity key = `(Study, causal_procedure_class, analysis_population/dataset_context)`.
- `causal_procedure_class`: closed vocabulary (two-sample MR, one-sample MR, randomized intervention, targeted perturbation, mediation, prospective survival cohort, and so on).
- `analysis_population/dataset_context`: the sample frame or source dataset set (a specific GWAS/QTL source, a cohort, a model-organism cohort).
Does not split on exposure, instrument, target, endpoint, arm, dose, direction, or estimator. This collapses drug-target MR from 11-12 to 1, and correctly keeps pQTL MR and eQTL MR separate, because their QTL source datasets differ (which is why all three runs already agreed on that split).

**`CausalLink`. Foundation entity. Primary synthesis count (Q4).**
Identity key = `(Workflow, exposure/intervention_family, normalized_outcome_domain, direction, biological_system)`.
- `exposure/intervention_family` and `normalized_outcome_domain` are normalized values from closed vocabularies, not raw endpoint or biomarker names.
Does not split on individual measured endpoint, assay, comparator, dose, timepoint, estimator, adjustment set, or subgroup. In the drug-target study, 11 distinct exposure families under one workflow give 11 links, which is correct; the error was minting 11 workflows. In the 17-alpha-estradiol study, one intervention across N normalized outcome domains gives N links, not 5/11/16.

**`Contrast`. Postcoordination axis cluster on a `CausalLink`. Not a Foundation entity. Never counted.**
Axes = `{comparator, arm, dose, timepoint, estimator, adjustment_set}`. Repeatable: a link carries a set of contrast clusters. One correction to your amendment: do not put the measured endpoint here. A contrast is the comparison structure and it is endpoint-independent (the same treated-vs-control-at-12-months, IVW contrast is read for many endpoints). Endpoint belongs to `ResultMeasurement`. Conflating the two reintroduces ambiguity at exactly the split point that failed.

**`ResultMeasurement`. Foundation leaf entity. Evidence grain. Never a claim-counting unit.**
Identity key = `(CausalLink, Contrast, endpoint_specification, assay/instrument, unit)`.
Attributes: point estimate, interval, p-value or statistic, n, effect direction. Countable only in an audit/evidence-density view.

**`Validation`. Foundation entity. Counted only as link-validation pairs (Q5). Never a link or workflow.**
Identity key = `(target_ref, validation_type, dataset/assay/system)`, `validation_type` from `{replication, rescue, orthogonal_assay, sensitivity, negative_control, challenge}`. Bears a necessary-condition relation to its target; excluded from workflow and link linearizations by construction.

Foundation entities: Study, CausalWorkflow, CausalLink, ResultMeasurement, Validation, SourceEvidence. Postcoordination only: Contrast and the normalized axes on links.

## 3. Is a distinct `ResultMeasurement` entity necessary?

Yes, and this is the load-bearing fix for link explosion. Link inflation happened because a reported endpoint had nowhere to live except by promotion to a link. Give each endpoint a first-class, non-countable home under a `(link, contrast)` pair and the upward pressure disappears: the model records every phenotype, biomarker, and assay as a measurement, and the link count stays fixed by the identity key. The entity is necessary precisely because it is not countable as a claim. That is what stops PDAP1 going to 30.

## 4. Retain, replace, or abandon?

Retain WHO as the sole methodology. Replacing it would not touch the failure, because no candidate framework supplies domain identity criteria; GO-CAM, PROV, and the rest would inherit the same blank and, being narrower on the reporting side, would force the PRISMA and evidence-table layer back on as bolt-ons. Abandoning single-model discipline reintroduces the undefined-unit-of-count problem the prior report was chosen to dissolve. The honest caveat: retaining WHO is necessary but not sufficient. The decisive lever is procedural determinism (question 5), not the framework label.

## 5. Revised prospective validation design (no second framework)

Everything below stays inside WHO Foundation, postcoordination, and linearization. The only genuine additions are deterministic identity functions (this is amendment A4 realized properly) and atom-first extraction.

**Development phase (current 15 reports, freely iterated).**
- Finalize the closed vocabularies: `causal_procedure_class`, `exposure/intervention_family`, `normalized_outcome_domain`, `biological_system`, `validation_type`.
- Freeze the five identity-key functions as code.
- Build the deterministic collapse: the model emits typed atoms with normalized attributes; Python computes workflow, link, contrast, measurement, and validation identity by hashing the keys. The model never returns a count.
- Extend your evidence-atom principle from quotations to individuation itself: the model's job is to classify, not to segment.

**Freeze.** Version the contract (v1.1.0). Vocabularies and identity functions are immutable after this point.

**Holdout phase (new, fully disjoint sample).**
- Draw 15 to 20 reports from the 357 minus every prior extraction, codebook, transfer-check, and now-development set. Keep the current 15 as development permanently, as you already decided.
- Pre-register the sample and the acceptance thresholds before any run.
- Run three isolated sessions per report, atom emission only.

**Two-layer measurement.**
1. Atom-level: Krippendorff's alpha on the decided attribute fields (`procedure_class`, `exposure_family`, `outcome_domain`, `direction`, `system`, `validation_type`). This is where residual disagreement now lives, and it is diagnosable field by field.
2. Derived-identity: run the collapse on each run's atoms and measure exact three-run agreement on workflow count, link count, design-family set, and validation-pair count. These are now pure functions of atom attributes, so any count disagreement traces to a specific attribute disagreement, not to opaque segmentation.

**Adjudication and open-world discipline.**
- A human curator resolves attribute disagreements; report model-vs-adjudicated agreement, not only model-vs-model.
- If the holdout surfaces an outcome domain or procedure class absent from the frozen vocabulary, log it as an open-world coverage event and do not silently edit the vocabulary. Coverage gaps are data (the Nickerson termination check), not test failures to be patched mid-run.
- Retain the boundary controls: prediction-only and non-molecular reports stay flagged, not silently admitted.

**Claims to make and avoid.** Report the counts descriptively with honest n; make no inferential or prevalence claim from a purposive holdout, and no claim that the model validates causal inference. Success means the derived counts are reproducible across runs and traceable to normalized atoms, which is exactly what v1.0.3 lacked.

---

This is a consultation response, not a repo change. If you want it recorded alongside the prior consultations (for example under `analysis/content_model_validation/`), tell me the target path and I will write it in sentence case to match the existing files.
