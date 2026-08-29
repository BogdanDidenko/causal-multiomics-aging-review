# Causal Extraction Run Artifact Contract

## Required directory layout

```text
data/causal_extraction/<suite-version>/<run-id>/
  orchestrator_manifest.json
  checksums.sha256
  preflight/
    git_state.json
    package_validation.json
    source_inventory.jsonl
  inputs/<report-id>/
    canonical_sections.jsonl
    coverage_ledger.json
  open_claim_discovery/<report-id>/<work-unit-id>/attempt-01/
  dense_claim_coverage/<report-id>/<work-unit-id>/attempt-01/
  frozen_candidates/<report-id>/
    candidate_inventory.json
    evidence_packets.jsonl
    freeze.json
  fixed_candidate_classifier/<report-id>/<candidate-ref>/repeat-01/attempt-01/
  final_claim_adjudicator/<report-id>/repeat-01/attempt-01/
  resolved/
    candidate_dispositions.jsonl
    final_claim_records.jsonl
    level_derivations.jsonl
    manual_review.jsonl
  reports/
    coverage_report.json
    schema_report.json
    stability_report.json
    provenance_report.json
```

Repeat directories continue through `repeat-05`. `attempt-02` exists only after a qualifying technical failure.

## Required files for every attempt

Each attempt directory contains:

- `rendered_prompt.txt`: exact prompt sent to Codex CLI;
- `rendered_prompt.sha256`;
- `template.sha256`;
- `output_schema.json` and `output_schema.sha256`;
- `input_payload.json` and `input_payload.sha256`;
- `request_metadata.json`;
- `raw_stdout.txt`;
- `raw_stderr.txt`;
- `raw_provider_response.json` when emitted by the provider;
- `parsed_response.json` when parsing succeeds;
- `validation.json`;
- `exit_status.json`.

`request_metadata.json` records suite version, prompt ID and version, report ID, work unit or candidate reference, repeat number, attempt number, model, reasoning effort, Codex CLI version, Git revision, worktree status, process start and end times, and retry reason.

## Immutability and provenance

The runner writes the rendered prompt and its hash before invoking the model. A retry must reuse the same hashes. Frozen candidates and evidence packets are append-protected after their freeze file is written.

The run-level checksum file covers every immutable input, prompt, schema, raw output, parsed output, validation result, disposition, and derived level. Reports are regenerated from immutable ledgers and do not replace them.

Model outputs contain short auditable rationales and evidence spans. Hidden reasoning is neither requested nor stored.

## Completeness checks

A run is incomplete when any of these conditions holds:

- a canonical section lacks its required open or dense core occurrence;
- a nonempty section was omitted or truncated;
- a frozen candidate lacks five terminal classifier outputs or an explicit technical-failure route;
- a candidate lacks a final disposition;
- an accepted claim lacks a valid codebook v0.2.0 record;
- an evidence quote is absent from its canonical section;
- a model-produced Level appears in a role output;
- a derived Level lacks an implementation hash and rule trace.

Incomplete items remain visible in `manual_review.jsonl` and denominator reports.

