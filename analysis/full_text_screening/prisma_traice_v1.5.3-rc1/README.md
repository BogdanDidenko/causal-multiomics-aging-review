# PRISMA-trAIce audit: deterministic full-text screening v1.5.3-rc1

## Scope

This directory freezes the auditable record of the 158-report full-text
eligibility run. It does not contain final human eligibility decisions or
causal evidence Levels 0-4.

The run used two criterion-level roles, five repeated calls per applicable
role, deterministic Docling section packaging, and Python-only routing rules.
The model pipeline produced 100 unanimous positive assessments, 33 unanimous
AI exclusions, and 25 records requiring human adjudication. These are interim
AI-assisted decisions until the prespecified human oversight and expert-gold
validation are complete.

## Preserved evidence

- `prisma_traice_audit_manifest.json` inventories and hashes the input,
  configuration, prompts, schemas, execution code, logs, and outputs.
- `manual_adjudication_queue_25_index.jsonl` links each unstable record to
  every relevant raw attempt by file and line number without reproducing the
  article text.
- `manual_adjudication_form_25.csv` is the empty human-decision ledger. It must
  be completed from the frozen evidence packets, not from newly generated
  model summaries.
- `ai_assisted_adjudication_draft_25.csv` is a transparent draft prepared from
  the frozen packets and existing five-run outputs. It is not an independent
  human decision and cannot replace the empty human-decision ledger.
- `restricted_archive_receipt.json` identifies the immutable local archive
  that contains the exact rendered prompts, raw responses, deterministic
  evidence packages, and the 25 record-level adjudication packets.

The restricted archive is excluded from Git because prompts contain licensed
or otherwise redistribution-limited article text. Its cryptographic receipt
allows the retained local artifact to be verified without publishing that
content.

The deterministic v1.5.4-rc1 routing amendment is reported separately under
`analysis/full_text_screening/routing_v1.5.4-rc1`. It preserves this frozen
25-record queue as historical pre-amendment evidence while reducing the active
queue through criterion-level logical short-circuiting without model reruns.

## Stage boundary

This run answers eligibility criteria IC1-IC5. `assessed` means eligible for a
subsequent causal-evidence extraction stage; it does not mean Level 2-4 and it
does not by itself mean inclusion in the final synthesis.

Levels 0-4 are a review-specific evidence taxonomy, not a PRISMA-trAIce
classification. They may be assigned only in a separately frozen extraction
stage that reports its input, prompt and schema versions, model settings,
Python mapping rules, repeated-run stability, human oversight, validation
against expert labels, and corrections. Evidence levels belong in extraction
and synthesis reporting; they must not silently modify the PRISMA eligibility
flow.

## Human adjudication

For each of the 25 records, the reviewer should inspect the deterministic
full-text package and all five criterion-level outputs recorded in the
restricted packet, then record one eligibility decision, the first failed
criterion when excluded, a short rationale, and supporting section IDs. The
human decision remains distinct from every AI output in the ledger.
