# Independent methodological review: causal extraction instrument v0.1.1-rc1

Read-only consultant report. Scope: the two-sample stability checkpoint, the frozen prompt suite,
the codebook, and the runner implementation. All numbers below were recomputed from the repository
artifacts, not taken from the summary documents.

## Context

101 reports passed full-text eligibility. The post-eligibility instrument is supposed to find causal
analyses, extract auditable evidence, classify design and identification, and let Python derive
Levels 0 to 4. The release candidate failed its prespecified gates. The question is not whether it
failed, it is *what actually failed*, and whether the numbers that look reassuring are real.

Short answer: the two most reassuring numbers in the checkpoint report are not measurements. The
derived-Level agreement figures compare empty result sets, and the candidate-status agreement figure
measures a deduplication task that the discovery stage created. The instrument's scientific
classification behaviour is essentially unmeasured.

---

## 1. Diagnosis

### 1.1 The derived-Level agreement statistics are vacuous and must be withdrawn

Recomputed from `analysis/causal_extraction/checkpoints/v0.1.1-rc1/checkpoint_*/candidate_stability.jsonl`:

| Checkpoint | Analysis-set candidates | Candidates producing a claim record in any run | Levels actually derived |
|---|---:|---:|---:|
| A | 20 | **0** | **0** |
| B | 16 | **1** | 5 (one candidate x 5 runs) |

In checkpoint A, all 20 candidates in the analysis set have `derived_outputs = [[],[],[],[],[]]`
across all five runs. Not one Level was derived. The published "20/20 (100.0%)" is twenty
comparisons of an empty list to an empty list.

In checkpoint B, 15 of 16 are likewise empty. The single candidate that exercised the Level
derivation path, `doi_884c15a783634c31::candidate-013`, returned levels **[3, 3, 3, 2, 3]**, a 4:1
disagreement.

So the observed derived-Level agreement, over units where the derivation actually ran, is **0 of 1**.
The correct statement is that derived-Level agreement is unestimated. The figures 100% and 93.8% are
not optimistic or conservative, they are undefined.

### 1.2 The classifier was never exercised on its primary job

Status distribution over all terminal runs in the analysis set:

| Status | A (100 runs) | B (80 runs) |
|---|---:|---:|
| `duplicate_or_overlapping` | 79 | 65 |
| `split_required` | 16 | 8 |
| `no_current_report_empirical_result` | 5 | 2 |
| `valid_single_claim` | **0** | **5** |

Modal status per candidate: `duplicate_or_overlapping` for 16 of 20 (A) and 13 of 16 (B).

The classifier's job is to fill a criterion-level claim record. In checkpoint A it did that zero
times in 100 opportunities. The "candidate status exact agreement 90% / 87.5%" is therefore
agreement on the label "this is a duplicate of another candidate", which is the easiest available
answer when discovery has nominated 86 to 103 near-duplicate candidates per report. It is not
evidence that the instrument classifies causal designs consistently.

### 1.3 What the 45% / 50% figure actually measures

Cross-tabulating status agreement against all-field agreement:

| | A | B |
|---|---|---|
| status exact **and** all fields exact | 9 | 8 |
| status exact, fields **disagree** | **9** | **6** |
| status disagrees | 2 | 2 |

In checkpoint A there are no claim records at all, so the only decision-driving fields left are
`duplicate_candidate_refs`, `split_proposals`, and `manual_review_reason`. Every one of A's nine
field-level disagreements is therefore a disagreement about **candidate boundaries and which sibling
a candidate duplicates**. None is a disagreement about causal design, identification, assumptions, or
result status.

All four `split_required` candidates across both checkpoints produced 5 of 5 distinct payloads. So
did B's single `valid_single_claim`. This is guaranteed by the implementation, see 1.4.

The two status disagreements in A are `split_required` versus `duplicate_or_overlapping` in both
cases. Again, boundary questions.

**Conclusion: the 45% / 50% figure is a measurement of free-text non-determinism plus an
over-generating discovery stage, not of causal-classification instability.**

### 1.4 The 100% all-field gate is unachievable by construction

`classifier_decision_payload()` at `src/causal_multiomics_aging_review/causal_extraction.py:632`
hashes the entire `claim_records` and `split_proposals` objects after removing only admin and
provenance keys. Free-text prose remains inside the exact-agreement hash:

`normalized_claim`, `exposure_or_intervention`, `exposure_operation`, `comparator`, `outcome`,
`population_or_model`, `biological_system`, `time_horizon`, `estimand_or_contrast.statement`, every
`assumption_judgments[].assessment` and `.search_note`, `diagnostics[].name` and `.result_or_role`,
`validations[].description`, `split_proposals[].split_note`, `manual_review_reason`.

Normalization is whitespace collapse and key sorting only (`_normalize_text`, line 380). Requiring
five independent generative runs to emit byte-identical scientific prose is a test of decoding
determinism, not a stability criterion.

Compounding this: `assumption_judgments`, `diagnostics`, `omics_roles`, `validations`, and
`variation_sources` are listed in `preserve_order_arrays`, so exact **ordering** is required. A
genetic-instrument claim carries nine required assumption domains, drawn from a 47-value enum.
Unanimity on their emission order across five runs has no scientific content.

The prespecified 100% gate could never have been met by any model. This should be stated plainly in
the write-up.

### 1.5 Genuine Python compression (relevant once records exist)

`candidate_level()` at `scripts/validate_causal_claim_records_v0_2.py:192` is a function of
`reviewer_identification_assessment` (5 values), plus `primary_design_or_method` only on the
`effect_claim_not_assessable` branch, plus the validation block only on the `effect_assessable`
branch.

The stability contract tracks **29 decision-driving field paths**. The Level reads one or two of them
plus one subrecord. Level agreement is therefore structurally near-guaranteed to exceed all-field
agreement, and will look high even when the underlying record is unstable. High Level agreement
certifies almost nothing about the auditable evidence record, which is what a synthesis actually
needs.

Any future report must present Level agreement alongside the marginal Level distribution and a
chance-corrected statistic. A constant classifier scores well on this metric.

### 1.6 Invalid denominators and hidden selection

**Survivorship conditioning on an outcome-correlated variable.** The analysis set is candidates with
5 of 5 grounded runs: 20 of 30 (A) and 16 of 30 (B). The 10 and 14 excluded candidates were excluded
because their runs failed *grounding*. Grounding failure is driven by evidence that is hard to quote
(hyphenated table text, symbol-dense passages), which is plausibly correlated with classification
difficulty. This conditioning biases agreement **upward**. The 45% and 50% figures are optimistic,
not conservative.

**Discovery-side incompleteness.** 11 of 15 reports in both checkpoints have incomplete grounded
discovery. Candidates were frozen from surviving work units only. Recomputed from
`report_stability.jsonl`:

- checkpoint A: **1,141 of 1,288 candidates (88.6%)** sit in reports whose discovery is known incomplete
- checkpoint B: **1,040 of 1,541 candidates (67.5%)**

The discovery prompts also instruct the model to silently drop what it cannot quote: "If no exact
supporting substring can be copied, omit that candidate or atom"
(`prompts/open_claim_discovery.txt:34`; equivalent wording in `dense_claim_coverage.txt:18`). That
directly contradicts `run_artifact_contract.md`, which declares a run incomplete when a nonempty
section is omitted, and the methodology's "Records and claims are never dropped". Recall loss is made
unmeasurable and is correlated with document formatting.

**The three-run sensitivity analysis is not a valid emulation of a three-run policy.** It restricts
to candidates with **five** valid runs. Under an actual three-run policy the eligible set differs:
17 B candidates had three clean runs versus 16 with five. The honest comparison is:

| | published | correct (units eligible under that policy) |
|---|---|---|
| A three-run | 11/20 (55.0%) | 11/20 |
| B three-run | 9/16 (56.2%) | **10/17 (58.8%)** |

Worse, three different numerators for this one statistic are in circulation:
`orchestrator_manifest.json` reports `candidates_first_three_exact` as 12 (A) and 11 (B) over all 30
sampled candidates, while `two_sample_stability.json` reports 11 and 9 over the five-valid subset.
Nothing reconciles them.

**Wilson intervals are wrong.** Candidates are clustered two per report across 15 reports. Wilson
assumes i.i.d. Bernoulli draws. Use a cluster bootstrap over reports.

**Report-uniform, not population-representative.** Two candidates were sampled per report regardless
of whether that report contributed 13 candidates or 313. The estimand is stability over a
route-balanced, report-uniform sample, which is neither the candidate population nor the
production-relevant denominator. Say which one is intended.

### 1.7 Leakage

**Checkpoint A is exactly the codebook development sample.** Verified: all 15 checkpoint-A DOIs
appear in `analysis/causal_extraction/codebook_pilot_v0.1.0/reports_15.csv`, a 15 of 15 overlap. The
design file records this as `prior_human_codebook_annotations_exist: true`. Codebook v0.2.0, its
split rules, assumption domains, and boundary cases were written while reading these exact papers.
Additionally, per `CHANGELOG.md`, prompt suite v0.1.1-rc1 was derived from a v0.1.0-rc1 smoke window
run on checkpoint A. **A is doubly in-sample: codebook-developed and prompt-tuned on it.**

**A and B are not exchangeable.** A is a purposive maximum-diversity sample with 15 distinct
`design_diversity_role` archetypes (CRISPRi multiome, heterochronic parabiosis, two-sample MR,
aged FMT, and so on). B has `design_diversity_role` empty for all 15 and is an unstratified
deterministic hash sample; it includes a 6,538-character, 2-section record that is a proceedings
abstract rather than a full text. Presenting "A 45% versus B 50%" as a replication compares different
estimands over different populations.

**Measurement-rule leakage into B's denominator.** B's classifier outputs were validated under runner
logic revised while inspecting A: the grounding retry, the quarantine rule, field-anchor validation,
and claim-ID canonicalization. Scientific inputs stayed frozen, so this is not label leakage, but the
rule that *defines the denominator* was tuned on A. That must be disclosed. Note also that A's
classifier responses were revalidated after the fact ("Revalidate 44 already-saved classifier
responses without new provider calls"), so A's grounding-failure count is not a clean prospective
measurement either.

### 1.8 Contradictions among prompt, schema, codebook, and gates

1. **`field_anchors` semantics are triply inconsistent.** The codebook (line 500) says field anchors
   "must reference evidence". The prompt says to use them when content "comes from a different
   section". The runner (`causal_extraction.py:578-589`) validates them as **section IDs**. The
   schema types them as bare strings with no description. This single mismatch produced **1,295 of
   2,220 recorded grounding failures (58.3%)**.
2. **`evidence_anchor_ids` reference objects that have no IDs.** `$defs/evidence_anchor` has no `id`
   property, yet `assumption_judgment`, `diagnostic`, and `validation` all *require*
   `evidence_anchor_ids`. Referential integrity is unenforceable and unenforced. Every assumption,
   diagnostic, and validation evidence link in the instrument is currently unverifiable.
3. **`claim_id` pattern versus candidate reference format.** The schema pattern `^[a-z0-9._-]+$`
   forbids `:`, but candidate refs use `::`. Four separate runner revisions in checkpoint A were spent
   on this (`__claim` versus `::claim` canonicalization). It is the likely cause of A's three schema
   failures, and it is a prompt/schema contradiction, not a model error.
4. **Partial sources may yield a valid claim.** The schema conditional at
   `fixed_candidate_classifier.schema.json:236-264` permits `candidate_status: valid_single_claim`
   with `full_text_status: partial`, forcing only `reviewer_identification_assessment: unclear`. The
   methodology says a partial source "cannot support a definitive classification and is routed to
   manual review". The schema permits a path the methodology forbids.
5. **`validations_proposed_by_report` is constrained in one direction only.** `one_or_more` requires a
   non-empty `validations` array, but a non-empty array is permitted alongside `none`. A
   Level-4-qualifying validation can therefore be attached to a claim that reports no validation.
   Separately, `SET_ARRAYS` in the runner and `sort_set_like_arrays` in the stability contract both
   list `validations_proposed_by_report`, which is a string enum, not an array.
6. **`extraction_mode` is a run configuration in the agreement hash.** Python knows it. Asking the
   model to emit it, and then requiring five-run unanimity on it, is a gratuitous disagreement
   channel. Same for `source_adequacy.sections_available`, which Python can read off the canonical
   section list.
7. **Prespecified analyses were never produced.** `analysis_plan.md` requires per-field five-run
   agreement, the 4:1 and 3:2 disagreement pattern distribution, and pairwise Jaccard for set-valued
   fields. None appears in the stability report. This is precisely the output that would have made
   the diagnosis in 1.3 visible at the time.
8. **Pre-classification assertions were declared but not enforced as blockers.**
   `coverage_contract.json` requires `omitted_nonempty_section_count: 0` before classification. In
   practice, grounding failures were quarantined and classification proceeded on reports with
   provably incomplete inventories in 11 of 15 cases.

---

## 2. Proposed unit and data model

### 2.1 Why the atomic claim candidate is the wrong primary unit

The evidence is unambiguous:

- 1,288 and 1,541 candidates from 15 reports (86 and 103 per report; **313 from a single randomized
  trial**). Extrapolated to 101 reports that is roughly 8,500 to 10,000 candidates, or about 45,000
  classifier calls at five repeats, before adjudication.
- 79% and 81% of classifier runs answered `duplicate_or_overlapping`. The dominant operation the
  instrument performs is deduplication, not classification.
- The atomic claim is a *derived normalization target*, not an observable. Its cardinality is set by
  how many endpoints, timepoints, and strata the authors happened to tabulate. That is a reporting
  artifact, and it means any claim-level tally is dominated by papers with large results tables.
- The codebook's own assumption modules are defined **per analysis**, not per contrast. You assess
  instrument strength and exclusion restriction once for an MR analysis, not once per endpoint.

### 2.2 The data model

A three-level nested model with a cross-cutting dimension and a typed relation.

**Level 1: report** (n = 101). Review unit, PRISMA row. Canonical document hash, source adequacy,
omics layers present, organism, study type.

**Level 2: causal analysis** (the primary extraction unit; expect 1 to 8 per report).
> One identification strategy applied to one exposure construct to one outcome construct in one
> system, as described in Methods and reported in Results.

This is where identification assumptions are defined and appraisable, and **this is where Levels 0
to 4 belong**. All expensive fields attach here: design, variation sources, assignment mechanism,
assumption judgments, diagnostics, identification assessment, method output type, contrast
components.

**Level 3: reported contrast** (0 to many per analysis, expect 1 to 50). One estimate or logical
result: endpoint, timepoint, stratum, direction, effect measure, value, uncertainty. Cheap,
table-shaped extraction with no identification judgment. `result_status` lives here and aggregates
upward. This is where reporting granularity is absorbed, without multiplying the expensive stage.

**Cross-cutting dimension: causal link** = (exposure construct, outcome construct, system). A
dimension table, not a row. Two analyses within or across reports may target the same link. This is
what makes same-link Level 4 validation computable, and it is what the Results section of the review
actually wants: how many independent analyses target link X to Y, at what identification level, from
which omics layers.

**Typed relation: validation edge** between two analyses (or an analysis and an external dataset)
within a report. Level 4 is inherently a relation between analyses. The current schema nests
`validations[]` inside a claim record, forcing the model to re-describe the other analysis in free
text, which is a significant and avoidable source of the disagreement observed.

**Retain the atomic claim as a derived view** (analysis x contrast row). Nothing conceptual is lost,
and the paper can still speak in atomic-claim language.

### 2.3 What this fixes

- `duplicate_or_overlapping` largely disappears: nominations merge deterministically on the
  (design, exposure construct, outcome construct, system) key, which the model already emits as
  enums. The model never adjudicates duplication.
- Denominators become defensible: "101 reports contributed N causal analyses targeting M distinct
  links". Reporting granularity no longer drives counts.
- Cost drops by roughly 1.5 orders of magnitude: about 400 analysis records instead of about 9,000
  candidates.
- The codebook needs minimal change. It already defines assumption modules per design, which is a
  per-analysis concept.

---

## 3. Deterministic evidence grounding

### 3.1 Measured failure taxonomy

All 2,220 grounding failure records across both checkpoints, reclassified by re-testing each failing
quote against the frozen canonical sections under a typography-tolerant normalizer:

| Class | n | % | Nature |
|---|---:|---:|---|
| `unknown_field_anchor:*` | 1,295 | 58.3% | Specification defect (see 1.8 item 1) |
| `unknown_section_id` | 253 | 11.4% | ID namespace mismatch or section pruned from packet |
| `quote_not_substring`, typography-recoverable | 362 | 16.3% | Soft hyphen, NBSP, dashes, quotes, Markdown, whitespace |
| `quote_not_substring`, correct text wrong section | 89 | 4.0% | Right passage, mis-attributed chunk |
| `quote_not_substring`, paraphrase or fabrication | 221 | 10.0% | Model-authored sentence, not in the document |

**About 90% is engineering. About 10% is genuine quotation fabrication.**

Per stage, `quote_not_substring` only:

| Stage | n | typography | wrong section | fabricated |
|---|---:|---:|---:|---:|
| `open_claim_discovery` | 225 | 68.4% | 0% | 31.6% |
| `dense_claim_coverage` | 302 | 28.8% | 29.5% | **41.7%** |
| `fixed_candidate_classifier` | 145 | 83.4% | 0% | 16.6% |

Two things follow. First, the dense coverage route is by far the least reliable quoter; its recall
contribution must be weighed against a 42% fabrication rate among its failures. Second, the
fabrications are real and consequential: for example `"Cordycepin required DAF-16 to extend
lifespan."` and `"DAF-16 is required for cordycepin-induced lifespan extension."` appear in
checkpoint A cited against three different chunk IDs. They are fluent, plausible, and absent from the
document. The exact-substring check is currently the only mechanism catching them, and it must not be
weakened.

### 3.2 The redesign: stop asking the model to reproduce text, ask it to point

**Anchor contract.** Every anchor is `{section_id, start, end}` character offsets into the frozen
canonical section, plus a `quote_echo` string. Python slices `section_text[start:end]`, and **that
slice is the quotation of record**. `quote_echo` is never the citation; it is a self-check signal.

**Validation becomes trivially deterministic:**

1. `section_id` in the frozen index, else `anchor_unknown_section`.
2. `0 <= start < end <= len(text)`, else `anchor_out_of_range`.
3. Slice non-empty and within a length cap, else `anchor_span_too_long`.
4. **Fabrication detector:** compare `normalize(quote_echo)` to `normalize(slice)`. On mismatch,
   record `echo_mismatch` with the normalized diff and a similarity score, and route to review. This
   preserves the fabrication signal as a graded, diagnosable flag instead of a run-killing binary.
5. Store `sha256(slice)` and `sha256(section_text)` in the anchor record.

**Make offsets easy to produce.** Render each canonical section to the model as numbered,
offset-labelled lines: `[L0142|off=8891] text...`. Accept
`{section_id, line_start, line_end, sub_start?, sub_end?}`. Line-granular anchoring is robust; Python
widens to the full line span when sub-offsets are absent or invalid and records
`anchor_granularity: line`. The citation stays exact and verifiable. This converts "did the model
retype punctuation correctly" into "did the model name a line range".

**Fallback locator ladder, executed by Python in fixed priority order:**

1. Exact offsets.
2. Exact raw substring (current behaviour, retained).
3. Normalized substring match against a precomputed normalization index, with an offset map back to
   raw text so the **raw** span is what gets stored. Normalization ladder, applied in fixed order and
   logged per anchor: NFKC, strip U+00AD soft hyphen, map Unicode dashes and quotes and primes to
   ASCII, map NBSP and thin, hair, and zero-width spaces to space, strip Markdown emphasis markers,
   collapse whitespace, casefold. Each rung is a named, versioned rule; the anchor records which rung
   matched, for example `match_rule: nfkc+soft_hyphen+ws`.
4. No match: `unresolved_anchor`. Never accept, never silently drop, always route to manual review
   with the failing string preserved.

**Full audit trail, append-only, in `resolved/anchors.jsonl`:** `anchor_id` (content-addressed),
`report_id`, `document_sha256`, `section_id`, `raw_start`, `raw_end`, `raw_text`, `sha256(raw_text)`,
`model_locator` as returned, `quote_echo`, `match_rule`, `match_rung`, `normalizer_version`,
`echo_similarity`, `validation_status`, `stage`, `repeat`, `attempt`.

Because anchors are content-addressed and carry a real `anchor_id`,
`assumption_judgments[].evidence_anchor_ids` finally has something to reference.

### 3.3 Specification bugs to fix alongside

- `field_anchors` must hold **anchor IDs**, not section IDs. Make schema, prompt, codebook, and
  validator agree. This alone removes 58% of recorded grounding failures.
- Add `anchor_id` to `$defs/evidence_anchor` and validate that every `evidence_anchor_ids` reference
  resolves.
- Unify the section ID namespace. Open windows and dense chunks currently emit different ID spaces
  (`chunk:0033` versus section IDs), producing 253 `unknown_section_id` failures. Give every canonical
  unit one ID and express windows and chunks as ranges over it.
- Freeze canonical text at the byte level with per-section SHA-256. A Docling re-run must invalidate
  anchors loudly rather than silently.

---

## 4. LLM versus Python division of labour

Principle: **the model emits closed-vocabulary judgments plus pointers. Python does arithmetic,
lookup, referential integrity, cross-field consistency, and rule application, and never parses
scientific prose.**

### 4.1 The model decides (closed enums plus anchor IDs, per analysis)

`author_claim_type`, `primary_design_or_method`, `supporting_designs_or_methods`,
`variation_sources[].{link_role, source}`, `assignment_mechanism`, `method_output_type`,
`reviewer_identification_assessment`, `result_status`, per-domain `assumption_judgments[].status`,
`diagnostics[].type`, `omics_roles[].{layer, qtl, role, scope}`, the six `contrast_components` flags,
`validations[].{validation_type, same_link_alignment, operation_alignment, data_independence,
experimental_independence, purpose, result_status, colocalization_threshold_met}`,
`source_adequacy.full_text_status`.

### 4.2 The model may write free text, but it never enters the agreement hash and never gates anything

`normalized_claim`, `reviewer_note`, `assumption_judgments[].assessment`, `.search_note`,
`validations[].description`, `diagnostics[].result_or_role`. These serve human readers and the
paper's narrative. Report them from the designated repeat or the adjudicated record. Do not compare
them across runs. This single change is the largest available gain in measured stability, and it
costs nothing scientifically.

### 4.3 The model must not emit these at all

`extraction_mode` (run config), `report_id`, `doi`, `claim_id`, `source_adequacy.sections_available`
(Python has the canonical section list), any Level, `contrast_complete`, `qualifies_for_level4`, and
the raw quotation text (section 3).

### 4.4 Python derives

`contrast_complete` from the six flags; `level4_status` from the validation tuple via the three
frozen codebook paths; `causal_evidence_level` via `candidate_level()`; all counts, denominators,
coverage ledgers, and PRISMA numbers. Store the rule trace and implementation hash beside each, as
already specified.

### 4.5 Python validates (new, and this is where the value is)

Deterministic cross-field consistency rules the model can currently violate silently:

- `validations_proposed_by_report == "none"` with a non-empty `validations` array.
- `contrast_components.comparator_specified == "yes"` while `comparator` is empty or "unclear".
- `assignment_mechanism == "randomized"` with no `variation_sources[].source ==
  "randomized_assignment"`.
- `primary_design_or_method == "genetic_instrument"` without the required genetic-instrument
  assumption domains present.
- `reviewer_identification_assessment == "effect_assessable"` with all `variation_sources` set to
  `observational_covariation`.
- `source_adequacy.full_text_status` in {partial, preview, unclear} with `candidate_status ==
  valid_single_claim` (resolve the schema versus methodology conflict in favour of manual review).

**Assumption-domain completeness, restructured.** The codebook already states that Python maps the
primary design to required domains and requires every domain to be present. Implement that map as a
frozen table and **have Python supply the domain list so the model only fills statuses**. The model
then returns a fixed-length, fixed-order status vector. This removes the array-ordering and
set-membership disagreement channel entirely, which is one of the two largest contributors to the
observed 45% figure.

**Referential integrity** of every `anchor_id`, every `duplicate_candidate_refs` entry, and every
validation-to-analysis link.

### 4.6 What Python must not do

Judge whether a comparator is "specified", merge claims semantically, or decide duplicates by reading
prose. Note the current design errs in the opposite direction: it hands the model a duplicate
detection task over up to 312 sibling summaries, which is neither a reliable language judgment nor a
Python job. Under the analysis-level model, duplicates collapse on an enum key and the problem
dissolves.

---

## 5. v0.2 pipeline architecture for 101 reports

**Stage 0, canonical freeze.** Docling to canonical sections under a single ID namespace, per-section
SHA-256, document SHA-256, line-offset index. Frozen, hashed, never re-derived mid-study.

**Stage 1, analysis inventory.** One call per report (or per Methods plus Results window pair for
long reports), 2 independent repeats. The model enumerates *causal analyses*: design enum, exposure
construct, outcome construct, system, plus anchors to the Methods sentence defining the procedure and
the Results sentence reporting it. Expect 1 to 8 per report. Deterministic union of the two repeats on
the (design, exposure, outcome, system) key. Non-matching analyses go to a reconciliation call, never
a silent merge.

**Stage 2, coverage audit.** Dense structural pass, 1 repeat, recall only. Same intent as the current
`dense_claim_coverage`, but its output is not a competing candidate stream. Per chunk it answers one
question: does this chunk describe or report a causal analysis absent from the Stage 1 inventory? Its
incremental yield is measured and reported, which is the discovery-route ablation the analysis plan
already prespecifies and the checkpoint never delivered. Given its 41.7% fabrication rate, it runs
under the offset contract and its additions must be confirmed by a Stage 1 style call before entering
the inventory.

**Stage 3, analysis classification.** Per frozen analysis, 3 repeats (see section 7). Python supplies
the design-specific assumption-domain vector. The model returns enums, statuses, contrast flags,
validation tuples, and anchor IDs. Free text is emitted but excluded from agreement.

**Stage 4, contrast rows.** Per analysis, 1 to 2 repeats. Structured extraction of endpoints,
timepoints, strata, and estimates from Results and tables. `result_status` aggregates upward.

**Stage 5, deterministic resolution.** Agreement evaluated on the **enum vector**, never on prose.
Unanimous resolves. Any enum disagreement, unresolved anchor, failed consistency rule, or `unclear`
on a Level-relevant field routes to adjudication.

**Stage 6, adjudication.** Model adjudicator on the disagreeing enum fields only, shown the competing
values with their anchors, blinded to repeat order. Residual goes to human. Every human override
logged with a reason.

**Stage 7, Python derivation.** `contrast_complete`, `level4_status`, `causal_evidence_level`, each
with rule trace and implementation hash.

**Stage 8, link graph and synthesis tables.** Analyses to links to Level distribution; validation
edges; cross-tabs by omics layer and design family. This is the Results section.

**Cost estimate.** About 101 x (2 inventory + ~10 coverage + ~4 analyses x 3 repeats + ~4 contrast)
= roughly **2,800 calls**, against roughly 45,000 under the current contract.

**PRISMA-trAIc compatibility.** Causal extraction remains a post-eligibility synthesis stage and does
not touch flow counts. Retain the existing per-attempt artifact contract. Add per-anchor provenance.
Report model and reasoning effort, prompt and schema hashes, repeat and retry policy, source
representation, section coverage, missing-text handling, human override counts, coverage-audit
incremental yield, and manual-review burden with explicit numerators and denominators. State that
Levels are internal appraisal labels, not eligibility categories or quality scores.

**Non-negotiable reporting additions.** Publish the per-field agreement table the analysis plan
already requires. Use cluster-bootstrap CIs over reports. Report every denominator, including the
excluded-run denominator and its reason.

---

## 6. Prespecified ablations and validation design

### 6.1 Set allocation

Of the 101 eligible reports: A (15) is burnt for codebook and prompt development. B (15) is spent as
a v0.1.1 checkpoint; **do not tune on it and do not reuse it as the sealed set**, its results are
already known. **71 reports remain untouched.**

| Set | n | Use |
|---|---:|---|
| DEV | 24 | All ablation and prompt iteration. May be inspected freely. |
| SEAL | 30 | Opened once, after one configuration is registered as final. |
| RESERVE | 17 | Untouched, for a possible later sealed re-test. |

Stratify DEV and SEAL on prespecified variables: primary design family (intervention, perturbation,
transfer, genetic instrument, mediation, directed or structural, prioritization-only), organism
(human, mouse, invertebrate, cell), and document size tercile. Deterministic seeded assignment;
publish the seed and the assignment table before running anything.

### 6.2 Gold annotation

Two domain experts annotate independently, blind to model output, at the **analysis** unit. Scope: all
analyses in DEV's 24 reports (estimate ~100 analyses) and all in SEAL's 30 (estimate ~120). A third
expert adjudicates.

**Publish inter-expert agreement before any model comparison.** If experts cannot reach
kappa > 0.6 on `reviewer_identification_assessment`, the construct is the problem, not the model, and
that is itself a publishable finding.

Also annotate analysis boundaries, so segmentation precision and recall are measurable, and ~200
anchor spans as ground truth for grounding accuracy.

### 6.3 Ablation table

All on DEV, all against the same expert gold, all with cluster-bootstrap CIs over reports.

| # | Factor | Arms | Primary metric | Acceptance threshold |
|---|---|---|---|---|
| A1 | Extraction unit | atomic claim (v0.1.1) vs causal analysis (v0.2) | units/report; boundary F1 vs expert; calls/report | Analysis unit: boundary F1 >= 0.75, <= 10 units/report |
| A2 | Grounding contract | exact substring vs offset + normalization ladder | % anchors resolved; fabrication detection on 200 gold spans | >= 99% resolved; fabrication recall >= 0.90 at <= 2% false flag |
| A3 | Free text in agreement hash | included vs excluded | 3-run enum-vector unanimity | Excluded arm >= 0.85 unanimity |
| A4 | Assumption vector | model-chosen domains vs Python-supplied fixed vector | per-domain status agreement (Krippendorff alpha) | alpha >= 0.70 |
| A5 | Discovery routes | open only / dense only / both | analysis-level recall vs expert; per-route fabrication rate | Dense pass must add >= 5% recall to justify its cost |
| A6 | Repeat count | 1 / 3 / 5 | unanimity rate, adjudication burden, agreement with gold | See section 7 |
| A7 | Reasoning effort | medium vs high | macro-F1 on `reviewer_identification_assessment`; cost | Adopt high only for >= 0.05 macro-F1 gain |
| A8 | Duplicate handling | model-adjudicated vs deterministic key merge | merge precision and recall vs expert | Key merge F1 >= 0.90 |
| A9 | Packet scope | anchor-adjacent sections vs full Methods+Results | identification-assessment accuracy | Larger packet must not degrade accuracy |

Register the table, metrics, seeds, and thresholds before running. Any factor failing its DEV
threshold is not carried to SEAL.

### 6.4 Metrics

Per-field macro-F1 and confusion matrices against expert gold; exact Level agreement and
quadratic-weighted kappa; within-one-Level agreement; boundary precision, recall, and F1; anchor
resolution rate and fabrication detection rate; Krippendorff alpha across repeats per field;
adjudication and manual-review burden; cost per report.

### 6.5 Sealed-set acceptance, registered in advance, single evaluation

- Reproducibility: 3-run enum-vector unanimity >= 0.85
- Grounding: anchor resolution >= 0.99; zero undetected fabrications in the audited sample
- Accuracy: macro-F1 >= 0.75 on `reviewer_identification_assessment` and on
  `primary_design_or_method`; quadratic-weighted kappa >= 0.70 on derived Level against
  expert-derived Level; within-one-Level >= 0.95
- Segmentation: boundary F1 >= 0.75
- Feasibility: <= 40 calls per report; manual-review burden <= 20% of analyses

Missing any threshold means the instrument is not released for unsupervised synthesis. It may still
be released as a human-assisted extraction aid, which is a legitimate and publishable outcome.

---

## 7. Five-run recommendation

**The original rationale does not transfer.** The methodology justifies five runs by analogy to
screening, where a unanimous exclusion rule is conservative in a defined direction. Here unanimity is
not conservative, it is a **routing rule** whose only effect is to allocate human workload. There is
no false-negative asymmetry to protect.

**The current data cannot settle it.** At n = 20 and n = 16, with free text inside the hash, the
five-run and three-run results differ by 2 and 1 candidates. The Wilson interval on 45% at n = 20
spans 0.26 to 0.66. Any stopping rule fitted to these numbers would be overfitting, which is exactly
what must be avoided.

**Recommendation, on design grounds rather than from these results:**

- **Move to 3 repeats as the registered v0.2 default**, and treat repeat count as prespecified
  ablation A6 on DEV, confirmed once on SEAL. Justification independent of current results: five runs
  cost 67% more than three for an incremental unanimity signal that only matters when per-run error
  is high, in which case unanimity is the wrong instrument anyway. With free text removed and the
  assumption vector fixed by Python, per-run variance should fall sharply, lowering the marginal
  value of runs 4 and 5 further. Three runs still distinguish unanimous, 2:1, and three-way split,
  which is all the routing rule consumes.
- **Adaptive stopping is defensible if prespecified.** Run 2. If the enum vectors are identical, stop
  and resolve. If not, run a 3rd; if 2 of 3 agree exactly, still route to adjudication, preserving
  the no-majority-vote principle; if all 3 differ, route to human. Escalate to 5 only for a
  prespecified high-stakes subset: analyses whose derived Level is 3 or 4, or that carry a Level 4
  validation path. This concentrates repeats where the review's conclusions are actually sensitive.
  **Report the realized run-count distribution**, because adaptive stopping makes the denominator
  run-dependent, which is precisely the flaw in the current 3-versus-5 comparison.
- **Fix the denominator prospectively, whatever is chosen.** Evaluate a k-run policy only on units
  with k valid runs *under that policy*, and report the excluded units with reasons. Never compare a
  three-run rate computed on the five-run survivor set.
- **Do not run 7.** The methodology is right that it would require two new preregistered runs, and
  there is no evidence it would help.

---

## 8. Salvage and reject decisions

### 8.1 Retain, and genuinely publishable as instrument-development evidence

- **The full protocol lineage**: methodology, analysis plan, coverage contract, stability contract,
  run artifact contract, prompt suites v0.1.0-rc1 and v0.1.1-rc1, codebook v0.2.0, the two-sample
  design, the feasibility amendment, and the orchestrator manifests with revision histories. This is
  an unusually complete and honest preregistration-and-deviation record, and it is the strongest
  asset in the project.
- **The feasibility result**: exhaustive atomic candidate discovery yields 86 and 103 candidates per
  report, up to 313 from one randomized trial, implying roughly 45,000 model calls for 101 reports at
  five repeats. A legitimate, citable negative result about extraction granularity.
- **The grounding failure taxonomy** in section 3.1: 2,220 failures, roughly 58% field-anchor
  specification defect, 11% ID namespace, 16% typography, 4% mis-attribution, 10% genuine
  fabrication. A useful and novel contribution, showing that a naive verbatim-substring grounding gate
  mostly measures typography, while fabricated but fluent quotations occur at a low, non-zero rate
  that only such a gate detects.
- **The finding that a 100% five-run exact-agreement gate over records containing free text is
  unachievable by construction**, with the demonstration that its failures were about candidate
  boundaries rather than causal classification.
- **The FAIL verdict itself**, and the decision to declare it rather than repair inside the frozen
  checkpoint. Report that as good practice.
- Checkpoint B may be described as a disjoint technical-feasibility replication of the **engineering**
  measurements only.

### 8.2 Reject from scientific synthesis

- Every candidate, claim record, disposition, and derived Level from checkpoints A and B. No expert
  gold exists; nothing here establishes accuracy.
- The candidate inventories (1,288 and 1,541) as counts of causal claims in these reports. They are
  nomination counts under a superseded granularity, with 11 of 15 reports knowingly incomplete and
  prompt-instructed silent omission of unquotable candidates.
- **The derived-Level agreement statistics (100% and 93.8%) must be withdrawn entirely, not
  caveated.** They compare empty result sets. The one candidate that derived a Level disagreed 4:1.
- The candidate-status agreement figures (90% and 87.5%) as evidence of classification stability.
  They are dominated by `duplicate_or_overlapping`, an artifact of over-nomination.
- The A-versus-B comparison as a replication (different sampling frames, different stratification, A
  doubly in-sample).
- The three-run versus five-run comparison as published (survivor-conditioned denominators; three
  inconsistent numerators in circulation).
- All Wilson intervals as reported (clustering ignored).

### 8.3 Required corrections before either checkpoint artifact is cited

In `two_sample_stability.md` and `two_sample_stability.json`:

1. Withdraw the derived-Level row; replace with "not estimable, 0 of 20 (A) and 1 of 16 (B)
   candidates produced a claim record; the single derived case disagreed 4:1".
2. Re-denominate the three-run row and reconcile it with the orchestrator manifests.
3. Add the candidate-status distribution, showing zero `valid_single_claim` in checkpoint A.
4. Add the excluded-candidate denominator (10 of 30 and 14 of 30) and the reason.
5. Replace Wilson intervals with cluster bootstrap over reports.
6. State the checkpoint A leakage explicitly: it is the codebook v0.2.0 development sample and the
   prompt-tuning sample.
7. State that reports with incomplete grounded discovery hold 88.6% (A) and 67.5% (B) of the frozen
   inventory.

---

## 9. Prioritized next actions

### 9.1 The smallest technically sound experiment before touching 101 reports

**E0: grounding-contract bake-off on 6 DEV reports, no scientific classification at all.**

Take 6 reports from the untouched 71, stratified by document size and by whether the source is
table-heavy. Run only a Stage 1 style analysis inventory under two arms:

- Arm i: current verbatim-quote contract.
- Arm ii: offset and line-locator contract with the normalization ladder and the `quote_echo`
  fabrication check.

2 repeats each. Measure anchor resolution rate, fabrication detection against a 60-span hand-checked
subsample, analyses nominated per report, and wall-clock cost. Roughly 6 x 2 x 2 x ~4 windows, about
100 calls, one afternoon.

**Acceptance to proceed:** arm ii resolves >= 99% of anchors, flags every hand-confirmed fabrication,
and yields <= 10 analyses per report.

**Why this first:** grounding is the single largest failure source (2,220 records), roughly 90% of it
is fixable engineering, and nothing downstream is measurable until anchors resolve deterministically.
10 of 30 and 14 of 30 candidates were excluded from the current stability analysis for grounding
reasons alone.

### 9.2 Ordered action list

1. **Correct or withdraw the two checkpoint stability artifacts** per 8.3. Do this first; it is a
   scientific-record issue, not a development task.
2. **Fix the four specification contradictions**: `field_anchors` semantics across schema, codebook,
   prompt, and runner; missing `anchor_id` on evidence anchors; section-ID namespace unification; the
   partial-source versus `valid_single_claim` schema and methodology conflict.
3. **Run E0.**
4. **Freeze the analysis-level data model** (section 2) and the codebook v0.3 deltas. Keep the atomic
   claim as a derived view.
5. **Partition the 71 untouched reports** into DEV 24, SEAL 30, RESERVE 17 with a published seed.
   Register the split before inspecting any of them.
6. **Commission expert gold annotation on DEV.** Publish inter-expert agreement before any model
   comparison.
7. **Register the ablation table (A1 to A9) and thresholds.** Run on DEV only.
8. **Register one final configuration. Single sealed evaluation on SEAL.**
9. **Only then run the 101-report production extraction**, carrying the sealed-set estimates into the
   paper as the instrument's measured performance.

### 9.3 One expectation to set now

Even a successful v0.2 will not be an unsupervised pipeline. Plan for a human-adjudicated fraction,
budget the expert time for it, and report it as part of the method rather than as a shortfall.

---

## Verification of the findings in this report

Every quantitative claim above is reproducible read-only from the repository:

- Empty derived outputs and the 4:1 Level disagreement: parse
  `analysis/causal_extraction/checkpoints/v0.1.1-rc1/checkpoint_{A,B}/candidate_stability.jsonl`,
  filter to `valid_response_runs == 5 and grounding_valid_all`, inspect `derived_outputs`.
- Status distributions and the status-versus-field cross-tab: same file, `candidate_statuses`,
  `five_run_exact`, `decision_hashes`.
- Coverage loss: `checkpoint_{A,B}/report_stability.jsonl`, `grounded_discovery_complete` weighted by
  `inventory_candidate_count`.
- Grounding taxonomy: `data/causal_extraction/v0.1.1-rc1/checkpoint_*_15_run1/**/validation.json`,
  `grounding_failures[]`, re-tested against `inputs/*/canonical_sections.jsonl`.
- Codebook leakage: intersect checkpoint A DOIs in
  `protocol/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_design.json` with
  `analysis/causal_extraction/codebook_pilot_v0.1.0/reports_15.csv` (15 of 15).
- Level compression: `scripts/validate_causal_claim_records_v0_2.py:192`.
- Free text in the agreement hash: `src/causal_multiomics_aging_review/causal_extraction.py:615-640`.
- Exact-substring grounding: same file, lines 357-377 and 570-603.
