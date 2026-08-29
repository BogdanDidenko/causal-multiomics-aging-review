# Causal Claim Extraction Methodology v0.1.0-rc1

## Status and purpose

This release candidate defines the post-eligibility causal claim extraction instrument for the 101 reports retained after full-text screening. It is frozen before the first model call. It does not alter study eligibility, PRISMA flow counts, or the frozen title/abstract and full-text screening instruments.

The instrument adapts the route-taxonomy workflow used in the earlier review:

1. open discovery over complete canonical Docling text;
2. an independent dense structural coverage pass;
3. deterministic union, provenance validation, and candidate freeze;
4. five repeated classifications of each immutable candidate;
5. deterministic resolution of exact agreement and model adjudication of disagreements, splits, and merges;
6. Python derivation of causal evidence Levels 0-4.

The model never assigns a causal evidence level. The model extracts and classifies criterion-level scientific facts under codebook v0.2.0. Python applies the published logical rules.

## Review unit and analysis unit

- Review unit: one eligible report.
- Extraction unit: one atomic causal claim, defined as one exposure or intervention operation linked to one outcome under one comparator, biological system or population, and time frame.
- Candidate unit: a provisional claim boundary nominated during discovery. A candidate may later be accepted, split, merged, excluded as background, or routed to manual review.

Claims are split when the operation, endpoint, system or population, comparator or time frame, identification strategy, or reported direction materially differs. Null, positive, negative, mixed, and conflicting results are retained.

## Frozen source representation

The authoritative source is canonical Docling output with stable section IDs and a document SHA-256. Graph-derived metadata may be retained as a side artifact, but it is excluded from model evidence packets and cannot establish a claim.

Each quoted assertion must be a verbatim substring of the section identified by `section_id`. Tables, captions, footnotes, supplements included in the canonical Docling package, and ordinary paragraphs are eligible evidence. Page limits and relevance ranking are prohibited.

Source adequacy is assessed before classification. A partial, preview-only, corrupt, or internally inconsistent source cannot support a definitive classification and is routed to manual review.

## Stage 1: open claim discovery

The report is packaged into deterministic, heading-aware, contiguous windows in source order. Every canonical section is a core section in exactly one window. Adjacent context may be repeated and is labeled separately. No section may be truncated or omitted.

`open_claim_discovery` nominates:

- every current-report empirical causal, directed, mechanistic, mediation, intervention, perturbation, instrumental-variable, temporal, or prioritization claim;
- atomic exposure, operation, comparator, outcome, system, population, and time fields when available;
- exact evidence anchors;
- relevant design, assumption, diagnostic, result, omics, validation, and limitation evidence atoms.

The prompt does not assign Levels 0-4 and does not reject a candidate because identification appears weak.

## Stage 2: dense structural coverage

The same canonical text is independently divided into deterministic structural chunks and packed in source order. Every canonical section is represented in exactly one dense core chunk; oversized sections are split at deterministic paragraph or sentence boundaries and receive stable derived IDs.

`dense_claim_coverage` repeats the candidate and evidence search without access to Stage 1 outputs. Its purpose is recall auditing. Dense-only candidates remain in the inventory until explicitly dispositioned.

## Candidate union and freeze

Python performs exact normalization only: whitespace normalization, DOI normalization, exact quote validation, and removal of byte-identical duplicate nominations. Python does not interpret scientific meaning and does not semantically merge claims.

The union of open-discovery and dense-coverage candidates is assigned stable `candidate_ref` identifiers in document order. The following artifacts are frozen and hashed before classification:

- canonical document package;
- coverage ledger;
- candidate inventory;
- evidence packets;
- codebook, prompts, schemas, runtime configuration, and source code.

Candidates cannot be silently deleted after freeze. Every `candidate_ref` must receive one final disposition.

## Stage 3: fixed-candidate classification

`fixed_candidate_classifier` receives one immutable candidate, its canonical evidence packet, and codebook v0.2.0. Five isolated Codex CLI sessions classify the same candidate with GPT-5.6 Terra and `reasoning_effort=medium`.

The classifier returns one of these statuses:

- `valid_single_claim`;
- `split_required`;
- `duplicate_or_overlapping`;
- `background_or_cited_work`;
- `no_current_report_empirical_result`;
- `context_only`;
- `insufficient_source`.

A valid claim output contains the complete criterion-level record required by codebook v0.2.0. The output includes author wording, identification assessment, variation source, assignment mechanism, contrast components, assumptions, diagnostics, omics roles, validation, result status, and exact evidence anchors. It excludes any model-assigned Level.

## Stability rule

Exact agreement is evaluated over candidate status and all decision-driving fields used by Python to derive the evidence level. Quote order, reviewer notes, and formatting are excluded after deterministic normalization; quote text and section grounding are validated separately.

- Five-of-five exact agreement permits deterministic resolution for a valid single claim or a clear non-claim disposition.
- Any disagreement, proposed split, proposed merge, source insufficiency, invalid quote, or unresolved schema failure enters adjudication.
- Stability is reported separately from criterion validity against expert labels.

Five runs were selected before production because the exclusion-style decision rule used in screening required unanimous repeated evidence, and because five independent sessions can distinguish unanimous, 4:1, 3:2, and more fragmented patterns while keeping the checkpoint workload tractable. Sensitivity analyses will recompute decisions from the first 3 runs and all 5 runs. A future 7-run analysis requires two additional preregistered runs and cannot be inferred from the five-run data.

## Stage 4: final claim adjudication

Stable claims are resolved by Python. Reports containing disagreements, split or merge proposals, duplicate candidates, or source problems are sent to `final_claim_adjudicator` with candidate order blinded to discovery route and repeat order.

The adjudicator receives all frozen candidates, the five classifier outputs, canonical evidence, and codebook v0.2.0. It must disposition every candidate and return final atomic claim records. The adjudicator runs five times in isolated Terra sessions. Unanimous decision-driving outputs are accepted. Remaining disagreement is retained for human adjudication; no majority vote is used.

The adjudicator is a same-model reconciliation role. It is not described as an independent human reviewer.

## Deterministic level derivation

Python derives Levels 0-4 from the final criterion-level record under codebook v0.2.0:

- Level 0: context or ineligible claim record;
- Level 1: association, prediction, prioritization, or unassessed identification;
- Level 2: formal directed hypothesis or an identification design that remains unassessable;
- Level 3: assessable causal effect with a defined contrast and reviewable assumptions;
- Level 4: Level 3 plus qualifying independent validation of the same causal link.

Colocalization, perturbation, replication, and other validation types qualify for Level 4 only under the link-specific rules in the codebook. The derived level, derivation trace, and implementation hash are stored beside the model output.

## Error and retry policy

Each call receives one retry only for invalid JSON, schema failure, timeout, or a provider execution error. The retry uses the identical rendered prompt, schema, model, reasoning effort, and input hash. Scientific disagreement is never retried as a technical error.

An unresolved technical failure, missing evidence, unsupported quote, incomplete candidate disposition, or incomplete coverage ledger routes the affected item to manual review. Records and claims are never dropped.

## Audit trail

Every model call stores the rendered prompt, prompt-template hash, output-schema hash, canonical input hash, request metadata, raw stdout and stderr, raw provider response, parsed response, validation report, retry state, model identifier, reasoning effort, Codex CLI version, Git revision, and timestamps. The artifact layout is defined in `run_artifact_contract.md`.

The frozen prompt files are the exact prompts used by the runtime. Runtime substitution may replace declared placeholders only. The final rendered prompt is persisted before execution.

## Pre-run and checkpoint gates

Before the first Terra call:

- all package hashes must match the manifest;
- all JSON schemas and configs must validate;
- prompt placeholders must match the declared runtime inputs;
- model name, reasoning effort, repeat count, and retry policy must match this document;
- coverage tests must demonstrate zero omitted and zero truncated sections on fixtures;
- the Git worktree must be clean at run start.

The first checkpoint uses 15 heterogeneous eligible reports selected before outputs are inspected. Required technical acceptance is 100% schema validity after retry, 100% quote grounding, 100% candidate disposition completeness, and complete section coverage. Stability is reported for every field and derived level; changes after the checkpoint require a new prompt-suite version and a new disjoint checkpoint set.

Expert validity remains a separate gate. Repeated agreement demonstrates reproducibility and cannot substitute for criterion-level expert evaluation.

