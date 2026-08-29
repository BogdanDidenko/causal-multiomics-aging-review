# Independent audit prompt

This is a normalized transcription of the invocation prompt. The invocation
contained the stale path
`protocol/causal_extraction/codebook/v0.2.0/causal_claim_codebook.md`; the
read-only auditor located and analyzed the canonical
`protocol/causal_extraction/v0.2.0/codebook.md` through repository search.

You are an independent senior methodological consultant for a systematic review
of causal multi-omics studies of aging. Work read-only. Do not edit files, do
not run model calls, and do not soften the critique.

Read and analyze these repository artifacts:

- `analysis/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_stability.md`
- `analysis/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_stability.json`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/methodology.md`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/analysis_plan.md`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/run_artifact_contract.md`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/coverage_contract.json`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/stability_contract.json`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/prompts/open_claim_discovery.txt`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/prompts/dense_claim_coverage.txt`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/prompts/fixed_candidate_classifier.txt`
- `protocol/causal_extraction/prompt_suite/v0.1.1-rc1/schemas/fixed_candidate_classifier.schema.json`
- `protocol/causal_extraction/v0.2.0/codebook.md`
- `protocol/causal_extraction/checkpoints/v0.1.1-rc1/classification_sampling_amendment.md`
- `analysis/causal_extraction/checkpoints/v0.1.1-rc1/checkpoint_A/orchestrator_manifest.json`
- `analysis/causal_extraction/checkpoints/v0.1.1-rc1/checkpoint_B/orchestrator_manifest.json`

Context: 101 reports passed full-text eligibility screening. This
post-eligibility instrument is supposed to identify causal analyses or claims,
extract auditable evidence, classify causal design and identification, and let
Python derive Levels 0-4. GPT-5.6 Terra Medium is run independently five
times. The desired production criterion is 100% repeated-run agreement on
decision-driving fields and exact evidence grounding.

Observed checkpoint results:

- Two disjoint report samples, A and B, each `n=15`.
- Discovery generated 1,288 and 1,541 atomic candidates, respectively.
- Classifier stability sample: two route-balanced candidates per report, 30 per
  checkpoint.
- Only 20 A and 16 B candidates had five fully grounded classifier runs.
- Exact agreement on all tracked decision fields: 9/20 (45%) and 8/16 (50%).
- Candidate-status agreement: 18/20 (90%) and 14/16 (87.5%).
- Python-derived Level agreement was reported as 20/20 (100%) and 15/16
  (93.8%).
- Discovery residual grounding failures after one retry: 31/340 and 36/380.
- Classifier terminal outcomes: A 118 ok, 29 grounding failures, 3 schema
  failures; B 107 ok, 43 grounding failures.
- The classifier sample has no expert gold labels, so these results establish
  no accuracy.
- A exposed several Python runner bugs. They were fixed with revision history
  before B classifier calls. Prompts, schemas, codebook, model, and report
  samples remained frozen.

Answer these questions rigorously:

1. Is the atomic causal-claim candidate the right extraction unit, or should
   the primary unit be study-level causal analysis, identifying contrast,
   causal-link family, or something else? Give a defensible data model.
2. Diagnose why detailed criterion agreement is low while derived Levels are
   high. Identify trustworthy stability and possible empty-output or Python
   compression artifacts.
3. Redesign evidence grounding so verbatim citation validity is deterministic
   and independent of reproducing punctuation, Markdown, whitespace, OCR
   artifacts, or Unicode. Keep a full audit trail.
4. Decide what the LLM should classify and what Python should derive or
   validate. Do not ask Python to interpret scientific prose.
5. Propose a practical next-version pipeline for all 101 reports that remains
   compatible with PRISMA-trAIc principles and supports the review Results.
6. Propose prespecified ablations on a new development set and a genuinely
   sealed set. Do not tune on checkpoint B. Include sample sizes,
   stratification, gold annotation, metrics, and acceptance thresholds.
7. Assess whether five runs remain justified. Compare 3, 5, and adaptive
   stopping without fitting a stopping rule to the current results.
8. State which v0.1 artifacts can remain as instrument-development evidence
   and which outputs must be rejected from scientific synthesis.
9. Give a prioritized next-action list, including the smallest technically
   sound experiment before processing all 101 reports.

Be specific enough to implement. Explicitly call out methodological errors,
leakage risks, invalid denominators, hidden selection effects, and
contradictions among prompt, schema, codebook, and acceptance gates. Produce a
structured report with diagnosis, proposed unit and data model, architecture,
ablation table, validation design, repeat-count recommendation, salvage/reject
decision, and immediate next steps.
