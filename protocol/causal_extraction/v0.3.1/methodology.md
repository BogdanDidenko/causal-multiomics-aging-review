# Causal extraction methodology v0.3.1

## Purpose

This prospective development ablation tests whether the poor stability of
`v0.3.0` came primarily from free candidate enumeration and evidence-anchor
selection. It does not authorize production causal extraction.

## Single changed factor

The same 12 reports, complete deterministic evidence-atom packets, causal
codebook, GPT-5.6 Terra Medium runtime, and five-repeat schedule are retained.
Candidate boundaries and candidate evidence IDs are fixed before the model
call. Terra classifies each supplied candidate but cannot add, remove, split,
merge, or choose evidence anchors.

The scaffold contains 45 candidates: 28 analyses and 17 rejected boundary
candidates from the analyst draft frozen before the `v0.3.0` calls. Candidate
IDs are opaque, and prompt-visible records contain only an identifying label
and source-ordered evidence IDs. They omit expected qualification, original
reference class, exclusion reason, analyst note, and causal Level.

## Input and output

Every call receives the complete report packet plus the report's fixed
candidate scaffold. No LLM, graph, embedding, lexical filter, or section
selector chooses report content. The model returns one closed classification
record per candidate and no quotations or evidence IDs. Python verifies exact
candidate coverage, attaches the frozen evidence IDs, sorts by scaffold order,
and derives Levels 2-4 for included candidates.

## Evaluation

Runs 1-3 form the prespecified three-repeat view, and runs 1-5 form the
five-repeat view. Exact report agreement includes every candidate decision and
every scientific field. Candidate qualification and field-level agreement are
reported separately to locate residual failures. Alignment with the frozen
analyst reference is provisional because it is not an independent expert gold
standard.

A pass would show that classification is stable once candidate discovery is
held fixed. Automated candidate-discovery recall remains a separate unresolved
gate before the remaining 89 reports can be processed.
