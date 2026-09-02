# Causal extraction methodology v0.3.0

## Purpose

This development instrument tests whether a short, design-level causal-analysis
codebook localizes the extraction task enough for reproducible GPT-5.6 Terra
Medium outputs. It supersedes the rejected v0.2 claim-level instrument for new
runs. It does not alter the completed eligibility screening or PRISMA counts.

## Development reference

Twelve purposively diverse reports were frozen before model output. An
AI-assisted analyst then produced a 28-analysis reference inventory and 17
rejected boundary candidates using exact evidence atoms. The inventory is
useful for development alignment and error analysis; it is not an independent
expert gold standard.

## Input representation

Python serializes every deterministic evidence atom from the canonical Docling
report in document order. Each section heading appears once, followed by atom
ID, atom type, and exact raw text. No LLM, graph, embedding, lexical filter, or
section selector chooses the supplied evidence. Reference-list atoms remain in
the packet because some Docling documents nest later STAR Methods under the
References heading; the prompt applies current-report attribution.

The context window is 131,072 tokens. A pre-run packaging audit must show that
every rendered prompt is at most 110,000 tokens and contains every atom exactly
once. This leaves at least 21,072 tokens for reasoning and structured output.

## Model and repeats

Every report is processed in five isolated Codex CLI sessions with
`gpt-5.6-terra` and reasoning effort `medium`. Runs 1-3 form the prespecified
three-repeat view; runs 1-5 form the five-repeat view. The five calls are made
once, so the two views differ only by the repeat prefix. One retry is allowed
for a technical or schema failure with an identical prompt and schema.

The model returns closed categorical fields and evidence IDs. It returns no
Level and no free-text rationale. Python validates IDs, orders analyses,
derives Levels 2-4, and computes exact agreement. Majority voting is prohibited.

## Evaluation

Exact report agreement requires identical source status and identical ordered
analysis records across all repeats, including evidence IDs and Python-derived
Levels. Field-level agreement and analysis-set agreement are also reported to
locate failures.

Reference alignment reports analysis recall, unmatched model analyses, boundary
promotions, and field differences against the frozen analyst draft. These are
development diagnostics rather than accuracy claims.

The instrument advances to the remaining 89 reports only after the five-repeat
exact-agreement gate is met or after a separately versioned revision is frozen
and evaluated. Any later expert validation is a distinct accuracy gate.
