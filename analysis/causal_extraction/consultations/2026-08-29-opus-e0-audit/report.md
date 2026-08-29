# Independent methods audit — causal-multiomics-aging E0 grounding bake-off

Auditor stance: read-only, no files edited. Sources: E0 protocol v0.1.0, inventory_template, semantic_audit_codebook, run1 summary.json, disagreement_analysis.json, disagreement_report.md, and the v0.1.1 failure/redesign decision. Throughout I separate what E0 preregistered from what was inferred post-hoc.

## Bottom line

- Grounding transport claim: **supported**, but the durable justification is structural (fabrication impossible by construction), not the small empirical delta.
- Inventory-instability claim: **directionally plausible but not an established result** — it rests on a post-hoc, gold-free, underpowered, contract-confounded metric that E0 never preregistered as a gate.
- Decision: **GO to E1** with evidence_atom_id fixed and the design-instance unit as the arm under test; **NO-GO** on importing any E0 inventory conclusion into the v0.3.0 rationale as if proven; **BLOCK** all accuracy/recall claims until the two-human gold is completed. E0's own proceed gate is currently unmet.

## 1. Are the two inferences supported by the denominators?

**Grounding ("evidence_atom_id solved technical citation transport") — supported, with a caveat on magnitude.**
- ID arm: first-attempt valid calls 66/66; retries 0; returned references 642/642 resolved (Wilson low 0.994).
- Quote arm: first-attempt valid 62/66 (0.939); 4 retries, all `quote_not_substring_of_supplied_atom`; terminally 66/66 valid, 393/393 resolved.
- Both arms reached 100% terminal resolution and both satisfied the preregistered gate "100% resolution after ≤1 retry." So the empirical superiority of the ID arm is only 4/66 first attempts. The real, durable win is the design guarantee the gate names separately: "zero model-authored citation text in the ID arm." Python resolves the span, so fabrication is impossible by construction, not merely rare. State the claim that way; do not lean on the 4-failure delta.

**Inventory ("open causal-analysis inventory failed stability") — directionally supported but weak and mis-headlined.**
- Headline all-pairs agreement is 15/33 (45.5%) per arm, but **every one of those 15 exact-agreement pairs is an empty window** (`all_fields_plus_grounding_exact` = both_empty = 15). On the 18 nonempty pairs per arm, full agreement is 0/18 in both arms, and 0/36 across arms. Relaxed metrics are also low (ID nonempty: analysis-count 7/18, closed-field 4/18).
- So the instability signal is real in direction, but the denominators are tiny: 18 nonempty pairs per arm, clustered in only 6 reports, unevenly distributed. Report-clustered uncertainty over 6 clusters is very wide. This can support "open inventory is not exactly reproducible on nonempty windows in this sample"; it cannot support a general "failed stability" verdict, and with no gold it cannot distinguish instability from inaccuracy at all.

**Preregistered vs post-hoc.** The stability numbers live in `disagreement_analysis.json`, explicitly tagged `status: exploratory_posthoc_not_prefrozen` and "not used to alter E0 prompts/schemas/outputs." The protocol only ever committed to *reporting* cross-repeat agreement "without treating free-text identity as a scientific gate" — there was **no preregistered stability threshold**. Therefore "reject open window-level inventory" is a post-hoc inference on an exploratory metric, not an E0 result. Good hygiene that this is labelled; the risk is that the redesign narrative later cites it as if it were a gated finding.

## 2. Is the design-instance unit scientifically defensible across methods?

Proposed unit: a design instance keyed by (identifying variation *or* assignment, exposure/intervention, biological system), with outcomes/readouts demoted to child contrasts.

- **Interventions (RCT/quasi):** clean fit. Assignment = key; treatment = exposure; readouts = contrasts.
- **Perturbations (CRISPR/drug):** strong improvement. Demoting readouts to contrasts directly fixes observed boundary failure #1 (perturbation split by histology/assay/phenotype). Highest-value change.
- **MR / single-exposure IV:** fits. Instrument = identifying variation.
- **MR/SMR multi-exposure screens:** **under-specified.** Keying on exposure construct implies one instance per exposure, so a multi-gene SMR screen explodes to N instances — contradicting the 1-8/report cardinality and re-opening boundary failure #2 (screen vs per-exposure) by fiat rather than rule.
- **Mediation:** **under-specified.** Exposure→mediator→outcome has no home for the mediator under a single exposure/outcome scaffold, and the "identifying variation/assignment" key does not capture sequential-ignorability. The mediator can be silently read as either exposure or outcome, reintroducing instability.
- **Causal discovery (DAG/SCM/invariance):** **poor fit.** These output a multi-edge graph, not a pre-specified exposure→outcome pair. "One instance per author-asserted directed edge" is workable but is itself a judgment call that can vary run to run.

Net: defensible and clearly better for design-based interventions/perturbations; incomplete for methods whose output is inherently multivariate (screens, mediation, discovery). The single-exposure/single-outcome scaffold is the weak point.

**Structural caution:** demoting outcomes to children stabilizes the *instance count* but risks pushing variance into ungated child fields — the same failure the v0.1.1 audit flagged (excluding free prose from the hash made byte-agreement meaningless). If contrasts are not themselves gated, the stability gain is partly illusory.

## 3. Smallest prospective E1 that localizes the task without tuning to these six reports

E0 confounded *unit* with *grounding*: the two arms differ only in grounding contract yet produced different inventories (cross-arm nonempty agreement 0/36; 642 vs 393 references; 152 vs 144 analyses). So E0 cannot attribute instability to the unit. E1 must isolate the unit factor.

Minimal design:
- **Fix grounding** = evidence_atom_id in both arms.
- **Single factor, two arms:** (A) open window-level inventory (v0.1.0 unit) vs (B) design-instance unit with child contrasts. Keep fixed atom-level role tagging *inside* arm B (or as a held-constant pre-pass) so you don't co-vary two changes; add it as a third arm only if budget allows.
- **New, disjoint reports:** 6-12 from the development partition, stratified by size tercile and table density, selected by structure/hash before any model call — explicitly not the six reports whose failure modes motivated the redesign.
- **Repeats:** hold at 2. The 3-vs-5 question is a separate preregistered ablation; do not bundle.
- **Primary metric (preregister):** exact repeat agreement on registered decision-driving enums + evidence-atom set at the instance level, **on nonempty-both pairs**, with report-clustered CIs. Report all-pairs and empty rate separately, never as the headline.
- **Anchor recall:** a small two-annotator boundary gold on the new reports, so empty windows can be scored as true negatives vs missed detections.

That localizes instability to the unit definition while breaking the grounding confound and avoiding overfit to the six E0 reports.

## 4. Threats to validity

1. **Empty-window agreement (primary threat).** ~45% of pairs are both-empty and account for 100% of exact agreement. Without gold, empty agreement conflates true negatives with shared misses. Mitigation: gate on nonempty-both; require a positive "no qualifying analysis" reason code so empties are auditable.
2. **Contamination / not sealed.** All six reports come from the 71-report pool that Luna profiled (all 101) and four article-design agents reviewed. Even E0's development data is model-exposed; no accuracy claim is admissible, and the redesign decision is being tuned on contaminated development reports. E1 on disjoint reports reduces but does not remove this (same pool).
3. **Output-contract coupling.** The report itself states the grounding contract changed upstream inventory behavior (0/36 cross-arm nonempty agreement; 63% more references in the ID arm). The arms are therefore not exchangeable — any cross-arm inventory comparison is confounded. The transport claim survives (mechanical); inventory comparisons do not.
4. **Pending human gold.** Verdict is `technical_pass_pending_human_semantic_audit`; status `pending_two_human_reviewers`. The 0.98 semantic-precision gate and the recall-non-inferiority gate are **unmet** — there is currently zero evidence on semantic support or on whether the ID arm loses analysis recall vs the quote arm. (Both reviewer forms share one template SHA, confirming no data yet.) Additional circularity: the two reviewers both define the boundary gold and adjudicate the very boundary task the codebook calls hard, on only 6 reports — inter-expert agreement must be reported first, before any recall claim.
5. **Underpowered stability denominators.** 18 nonempty pairs/arm across 6 clusters; the "reject open inventory" decision has weak support even as a stability claim.
6. **Positive controls (for balance).** Denominator hygiene is clean: 132 planned = 132 terminal, `failure_reasons {}`, all `ok`, coverage 6/6, gate requires failures in all denominators. The grounding Wilson intervals are tight (642 references). These parts are trustworthy.

## 5. Go / no-go

- **GO** to E1 adopting evidence_atom_id as the grounding interface — earned by clean technical denominators plus the structural anti-fabrication guarantee.
- **GO** to E1 treating the design-instance unit as the **hypothesis under test**, not a settled conclusion.
- **NO-GO** on writing "open inventory rejected / design-instance validated" into the v0.3.0 rationale as an established E0 result — it is post-hoc, gold-free, underpowered, and contract-confounded.
- **BLOCK** any accuracy, precision, or recall claim until the two-human semantic + boundary gold is completed; until then E0 is a technical pass only and its proceed gate is unmet.

## Actionable schema/prompt recommendations

1. **Rekey the unit (highest-value prompt edit).** `inventory_template.txt` currently keys on "one exposure construct, one outcome construct, one biological system" — outcome as a key is exactly what drives readout-splitting. Change to key on (design/identifying variation, exposure, system) and state explicitly that outcomes/readouts are child contrasts and never a split trigger.
2. **Add explicit construct slots** so multivariate methods aren't forced into a single exposure/outcome pair: `mediator_construct` (mediation), `instrument_set` (MR/MVMR/SMR), `graph_edge`/`node_set` (causal discovery).
3. **Deterministic screen/hit rule.** Preregister: a multi-exposure screen = one design instance; each reported exposure→outcome hit = a child contrast. Fixes boundary failure #2 and bounds cardinality.
4. **Causal-discovery rule.** One instance per author-asserted directed causal edge; the fitted graph is a diagnostic. Preregister to prevent per-run edge re-parsing.
5. **Gate the child contrasts.** Register contrast-level decision fields (result direction, estimate presence) in the agreement gate so stability isn't achieved by exporting variance into ungated free text (the v0.1.1 mistake).
6. **Split role tagging from assembly.** Make fixed atom-level role tagging a separate deterministic pass with its own agreement metric, so E1 can tell whether instability lives in tagging or in assembly.
7. **Empty-window reason codes.** Require a positive "no qualifying analysis (reason)" output for empty windows so empties are auditable as true negatives vs misses.
8. **Metric reporting rule.** Preregister nonempty-both agreement as primary; always report empty rate and all-pairs agreement separately; never headline the empty-inflated number.
