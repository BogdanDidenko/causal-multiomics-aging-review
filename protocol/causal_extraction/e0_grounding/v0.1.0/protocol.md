# E0 deterministic grounding bake-off v0.1.0

## Purpose

E0 tests the evidence-grounding interface before causal classification is
redesigned. It inventories report-level causal analyses and compares two ways
of citing the same frozen Docling evidence:

1. `verbatim_quote`: the model reproduces a quote and section ID;
2. `evidence_atom_id`: the model returns a stable atom ID and Python retrieves
   the exact source span.

E0 does not assign identification judgments, causal Levels, eligibility, risk
of bias, or scientific synthesis labels.

## Unit

A causal analysis is one design implementation applied to one exposure
construct, one outcome construct, and one biological system. Endpoint rows,
time points, strata, instruments, estimates, and sensitivity checks remain
children or diagnostics of that analysis. A report that applies MR and then a
CRISPR perturbation contributes two analyses.

Qualifying analyses use an effect-identification design or a formal directed
hypothesis method. Causal wording, association, prediction, enrichment,
colocalization alone, and an undirected network do not qualify without such a
method.

## Source representation

The source of record is
`data/full_text_screening/v1.5.3_deterministic_full_text_158/input.jsonl`.
No Docling Graph labels, graph rankings, Luna-generated profiles, or previous
causal candidates are supplied to the E0 model.

Python deterministically segments every canonical section into non-overlapping
sentence-level prose atoms or table-row atoms. A source unit longer than the
frozen maximum is split at a deterministic textual boundary. Every atom stores:

- document, section, and atom SHA-256 values;
- stable `evidence_atom_id`;
- section and document source order;
- raw Unicode-codepoint start and end offsets;
- exact unnormalized source text;
- page references when available.

All non-whitespace source characters are covered. Atom text is never rewritten
or normalized as the citation of record.

## Packaging

Evidence atoms are packed contiguously in canonical source order. Section
boundaries and identifiers are retained, including when one long section spans
multiple work units. Each evidence atom appears as core evidence in exactly one
work unit. Adjacent context may repeat.
No relevance ranking, graph selection, page cap, section truncation, or silent
omission is allowed.

Core and adjacent context obey frozen character and atom-count limits. The
atom-count limit controls serialization overhead in table-dense sections; it
creates additional contiguous work units and never drops content.

Before any model call, six candidate packaging configurations were compared
with the frozen `o200k_base` tokenizer. Selection minimized planned calls among
configurations whose largest rendered prompt stayed at or below 23,000 tokens,
then minimized the largest prompt. The complete zero-model-call calibration is
stored in `packaging_calibration.json`.

Both arms receive the same ordered evidence atoms and text. Their output
grounding contract is the only planned difference.

## Runtime

- model: `gpt-5.6-terra`;
- reasoning effort: `medium`;
- provider: isolated Codex CLI session;
- independent repeats: 2 per arm and work unit;
- schema-constrained JSON;
- one retry for technical, schema, identity, or grounding failure;
- identical rendered prompt on retry;
- no model-visible prior-run output.

## Sample

E0 uses six development reports outside checkpoints A and B. Within each
document-size tercile, deterministic selection chooses one low-table-density
and one high-table-density report. Selection reads document structure and
hashes only, before model output.

Earlier article-design agents inspected generated profiles for all 101 eligible
reports. E0 is therefore a development experiment. None of the remaining
reports is represented as genuinely sealed. A later sealed evaluation requires
an external or temporal sample acquired after the replacement instrument is
frozen.

## Technical metrics

- schema-valid terminal calls;
- resolvable grounding references;
- unknown atom IDs or section IDs;
- exact quote-substring failures;
- analyses without core evidence;
- complete core-window coverage;
- evidence references and analyses per report;
- calls and retries per arm;
- cross-repeat inventory and grounding-reference agreement, reported without
  treating free-text identity as a scientific gate.

## Semantic audit

Python can prove that an atom exists and recover its exact text. It cannot prove
that the passage scientifically supports the model judgment. E0 therefore
produces a blinded semantic-audit form containing a stratified sample of at
least 60 references. Two humans independently judge support before E0 can pass
its full proceed gate.

## Proceed gate

- 100% evidence-ID resolution after at most one retry;
- 100% core-atom coverage and zero silent work-unit omission;
- zero model-authored citation text in the ID arm;
- semantic-support precision at least 0.98 in the adjudicated reference audit;
- no lower expert-gold analysis recall than the quote arm;
- all numerators and denominators include technical failures.

Before human semantic adjudication, the strongest permitted verdict is
`technical_pass_pending_human_semantic_audit`.
