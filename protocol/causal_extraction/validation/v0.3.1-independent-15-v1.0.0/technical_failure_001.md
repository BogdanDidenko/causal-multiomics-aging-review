# Technical failure 001: CLI schema incompatibility

## Classification

This was a pre-inference technical failure. It produced zero valid scientific
annotations and provides no evidence about the causal-analysis codebook,
prompt, model accuracy, or inter-reviewer agreement.

## Observed failure

The run started from prospective freeze commit
`80f6659d2ee7909e947f7a0d0a15e2cfbf359898`. All 15 reports were attempted once
per reviewer with one identical technical retry. The result was 30 failed calls,
60 failed attempts, and zero normalized outputs.

- Codex CLI: the generic adapter removed `allOf` from three array fields and
  left them without a required `type`, so the Responses API rejected the schema.
- Claude Code CLI: the CLI validator did not resolve the declared Draft 2020-12
  metaschema URI and rejected the schema before producing an annotation.

The local failed-call snapshot remains under the ignored
`data/causal_extraction/v0.3.1_independent_validation/technical_failure_001/`
directory. Its compact cryptographic inventory is versioned in
`technical_failure_001.json`; prompts and full-text packets are not committed.

## Corrective action

Technical revision 1 inlines local `$ref` and `allOf` definitions, removes JSON
Schema dialect metadata for the CLI-facing copy, and retains the original frozen
schema for post-response validation. It does not change the 15 reports,
evidence atoms, annotation manual, task prompt, inherited codebook, output
fields, model settings, or retry policy.
