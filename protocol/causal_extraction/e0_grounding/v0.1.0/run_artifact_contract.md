# E0 run artifact contract

## Frozen protocol artifacts

The pre-model Git commit contains the protocol, runtime, sample, contamination
audit, both grounding contracts, both schemas, atomization code, runner,
summarizer, tests, deterministic packaging calibration, and a SHA-256 manifest.
The run aborts when any registered artifact or source-data hash differs from
the freeze.

## Restricted raw run

`data/causal_extraction/e0_grounding/v0.1.0_run1/` is ignored by Git because it
contains article text. It retains, for every call and attempt:

- exact rendered prompt and SHA-256;
- runtime JSON Schema and SHA-256;
- request metadata, model, reasoning effort, Git revision, and input hash;
- raw provider response, stdout, stderr, and parsed response;
- schema and grounding validation failures;
- Python-resolved evidence text, section, raw offsets, and hashes for valid
  calls;
- terminal status and append-only call ledger.

Canonical sections, the complete evidence-atom index, deterministic work units,
and the atom-coverage assertion are retained once per report. Failed and retried
attempts remain in place.

## Versioned compact trace

`analysis/causal_extraction/e0_grounding/v0.1.0_run1/` contains no article text.
It records aggregate metrics, a call ledger, raw-tree SHA-256, and a per-file
checksum inventory. Separate blinded reviewer forms, their concealed arm key,
and the adjudication form stay in the restricted raw run; the compact report
records their paths and hashes.

No failed call, empty output, retry, or omitted work unit may be removed from a
reported denominator.
