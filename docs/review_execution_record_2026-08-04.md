# Final-Review Execution Record: Path to the 135-Record Manual Queue

## Purpose and status

This is the authoritative navigation record for the final causal multi-omics
aging review as of 2026-08-04. It separates the frozen identification corpus,
the full-corpus model evaluation, the deterministic post-hoc routing correction,
and the first human-review queue. It does **not** claim that the current prompt
suite is validated or that any queue is a final included-study set.

The active research question is: *which empirical studies integrate at least two
molecular omics layers to investigate an aging process and report a formal
causal design or directed causal hypothesis?*

The current title/abstract suite is `v1.4.0-rc1`, with approval status
`sealed_holdout_pending_not_active`. Expert criterion-level gold labels and the
sealed validation evaluation remain outstanding. Therefore, these outputs are
an auditable prioritization instrument, not a validated exclusion instrument.

## The only lineage to use for the current manual screen

1. **Frozen identification, v1.1.2.** The 2026-08-02 search retrieved 12,528
   source records from PubMed, Europe PMC, Scopus, Semantic Scholar, scoped
   OpenAlex, and manual Google Scholar. DOI-first deduplication produced 7,858
   canonical records. The authoritative counts and source decisions are in
   [`search_execution_2026-08-02_v1.1.2.md`](search_execution_2026-08-02_v1.1.2.md).
2. **Abstract-bearing corpus.** Of those records, 5,022 had title/abstract text
   and 2,836 lacked an abstract. The latter are a metadata-enrichment/manual
   queue and were not screened or excluded by the agent pipeline.
3. **Frozen five-run model evaluation.** The 5,022 records were evaluated on
   2026-08-02 with GPT 5.6 Terra Medium through Codex CLI, `reasoning.effort`
   `medium`, and the frozen `v1.4.0-rc1` suite. The run used source revision
   `b73c7b2`, completed 96 shards, and retained all raw provider responses.
   The original run report is
   [`report.md`](../analysis/v1_full_corpus_screening_2026-08-02/report.md).
4. **Criterion-path correction, no model calls.** Commit `e4ed2eb` corrected
   the Python routing implementation to match the protocol: five identical
   *first-failed criterion paths* determine an automatic exclusion; drift in
   unrelated fields cannot override that path. Reapplying this rule to saved
   outputs changed 330 routes: 318 scope and 12 EC5 paths. The historic
   `seek_full_text` count of 1,972 becomes 1,642 under this corrected routing;
   the 401 metadata-protection routes remain retained. This correction does not
   modify raw model responses.
5. **Positive-causal candidate localization, no model calls.** There are 700
   original `positive_causal_basis` routes. Of those, 624 have exact agreement
   on every tracked scope and causal field across all five runs. The first
   manual title/abstract queue contains 135 records with all of the following:
   five-of-five tracked-field stability, an aging-process anchor in the title,
   and explicit current-report multi-omics evidence. Its source of truth is
   [`candidate_triage.csv`](../analysis/v1_full_corpus_screening_2026-08-02/existing_log_localization/candidate_triage.csv).

The reference study `10.1038/s41467-023-37729-w`, *Multi-omic underpinnings of
epigenetic aging and human longevity*, is in this 135-record queue. It has
five-of-five stable scope and causal outputs, with `genetic_instrument` as its
causal routing anchor.

## Current priority-1 report-retrieval subflow

The priority-1 queue now has a completed, PRISMA-aligned retrieval audit. This
is a bounded subflow for workflow reporting, not the final review denominator:

| Retrieval node | Records |
|---|---:|
| Priority-1 candidate records | 135 |
| Preprints outside this non-preprint retrieval batch | 16 |
| Non-preprint candidates audited | 119 |
| Abstract-only reports excluded before report retrieval | 6 |
| Reports sought for retrieval | 113 |
| Reports not retrieved or insufficient after conversion QA | 16 |
| Reports retrieved and sufficient for full-text assessment | 97 |
| Reports assessed for eligibility | pending |

The frozen retrieval snapshot initially archived 86 PDFs, 11 presumed-complete
publisher HTML files, and one XML. Docling conversion QA showed that one
Springer HTML was an access/challenge shell with metadata but no article body.
It was reclassified as insufficient, leaving 97 assessable full texts. This is
a retrieval correction, not a scientific eligibility exclusion. The dated
evidence is in
[`full_text_sufficiency_correction_v1.0.0.md`](../analysis/docling_graph/full_text_sufficiency_correction_v1.0.0.md).

The 16 preprints are outside this retrieval batch; this subflow does not declare
them finally excluded from the review.

The original machine-readable retrieval snapshot is
[`prisma_retrieval.json`](../data/full_text/v1.1.2_priority_1_nonpreprint_119/prisma_retrieval.json),
generated from the retrieval manifest and
[`retrieval_adjudication.csv`](../data/full_text/v1.1.2_priority_1_nonpreprint_119/retrieval_adjudication.csv).
The item-level browser evidence is retained in
[`manual_publisher_access_audit_2026-08-08.csv`](../analysis/full_text_retrieval/manual_publisher_access_audit_2026-08-08.csv).
The active downstream PRISMA count applies the conversion-stage correction.

Docling Graph evidence indexing was completed on 2026-08-09 for all 97
sufficient full texts with GPT 5.6 Luna Light. The run produced 97 graphs and
1,475 provenance-grounded nodes, with zero unresolved nodes and zero graph
extraction failures. This is preprocessing only; `Reports assessed for
eligibility` remains pending. The execution report is
[`execution_report_v1.0.0.md`](../analysis/docling_graph/execution_report_v1.0.0.md),
and the PRISMA processing record is
[`prisma_full_text_processing.json`](../data/full_text_graph/v1.0.0_luna_light/prisma_full_text_processing.json).

## What the 135 records mean

The 135 are the **first manual title/abstract triage queue**, not a final PRISMA
box, a final full-text queue, or a model-derived eligibility label. The textual
priority rule exists only to make the next human work tractable while preserving
all remaining positive and unresolved records for later adjudication.

Manual review of the 135 must answer the missing linkage question that the
current title/abstract contracts do not encode: does the stated causal design
test a causal relationship relevant to the report's multi-omics aging analysis,
rather than being a perturbation or intervention with omics measured only as a
downstream descriptive readout? Do not automatically exclude records outside
the 135 on the basis of this prioritization rule.

The 700 positive-causal routes are partitioned only for workflow ordering:

| Queue | Records | Definition |
|---|---:|---|
| Priority 1 | 135 | Stable five-run fields, aging-process title anchor, explicit multi-omics. |
| Priority 2 | 169 | Stable five-run fields and aging-process title anchor. |
| Priority 3 | 128 | Stable five-run fields and explicit multi-omics, without the title anchor. |
| Priority 4 | 192 | Other stable positive-causal candidates. |
| Manual title/abstract adjudication | 76 | Positive route without complete all-tracked five-run stability. |

The deterministic localization audit, including the 330 corrected routes, is
in [`existing_log_localization`](../analysis/v1_full_corpus_screening_2026-08-02/existing_log_localization/).

## Why five repeats were used

Five repeats were a frozen operational stability gate before the 2026-08-02
corpus execution, not a number selected after seeing the 135-record queue. The
frozen suite configuration has `repeats: 5`, a SHA-256 of
`8f3b4ec54d8cec21c43f3fb43561f8fc8d168abc83c0be8c6cf60d6c54f1d8f6`, and was
committed in `d025544` before runtime revision `b73c7b2`.

The rationale is operational, not a claim that five is mathematically optimal:

- Three outputs provide an initial unanimous-path test; two additional outputs
  test whether that apparent unanimity persists.
- The policy uses repeats as a conservative instability detector. It does not
  estimate a majority label, assume independent Bernoulli trials, or infer
  accuracy from agreement.
- The pre-specified rule retains any disagreement rather than treating it as an
  exclusion, so an additional repeat can only reveal instability in an early
  automatic exclusion.

The saved outputs show why the additional two repeats mattered. Among 4,549
records with five completed scope runs, first-three agreement on all tracked
fields was 3,858/4,549 (84.8%), while first-five agreement was 3,624/4,549
(79.7%). Runs four and five invalidated 61 early unanimous scope exclusions
(EC1=8, EC3=36, EC4=17) and five early EC5 exclusions. Thus, a three-repeat
unanimity rule would have automatically excluded 66 records that the five-run
policy retained.

This is a retrospective stability finding, not evidence that five is sufficient
for correctness. There are no seven-run outputs, so this study must not claim a
seven-run estimate or an optimal repeat count. A future seven-run analysis would
be a separately pre-specified sensitivity study after prompt and gold-standard
decisions are frozen. The machine-readable audit is
[`repeat_count_sensitivity.json`](../analysis/v1_full_corpus_screening_2026-08-02/repeat_count_sensitivity/repeat_count_sensitivity.json).

## Historical material that must not be mixed into this path

- The 2026-07-27 search snapshot is a superseded pilot and is not part of the
  v1.1.2 PRISMA denominator.
- `v0.99.0` and earlier prompts, 790 screening outcomes, and 9,515 raw model
  responses are rejected instrument-development history. Their directional
  wording criterion and lack of expert gold labels are documented in
  [`postmortem_v0.99.md`](../analysis/v1_methodology/postmortem_v0.99.md).
- Historic raw routing (`2,978` exclude, `1,972` seek full text, `72` manual)
  and corrected criterion-path routing (`3,308` exclude, `1,642` seek full
  text, `72` manual) are distinct analyses. The latter is a reproducible
  post-hoc correction, not a replacement for the archived raw-run report.
- The 135-record queue is not a PRISMA denominator and must not be reported as
  “studies included” or “full texts assessed.”
- The 98 retrieved reports are available for assessment but have not yet been
  assessed for eligibility. They must not be reported as included studies.

## Reproduction commands

Run these commands from the repository root. They use saved outputs and make no
model calls:

```bash
.venv/bin/python scripts/localize_existing_screening_candidates.py \
  data/screening/v1.1.2_full_corpus_96shards/input.csv \
  data/screening/v1.1.2_full_corpus_96shards/runs \
  analysis/v1_full_corpus_screening_2026-08-02/existing_log_localization

.venv/bin/python scripts/analyze_repeat_count_sensitivity.py \
  data/screening/v1.1.2_full_corpus_96shards/runs \
  protocol/screening/configs/prompt_suite_v1.4.0-rc1.json \
  analysis/v1_full_corpus_screening_2026-08-02/repeat_count_sensitivity
```
