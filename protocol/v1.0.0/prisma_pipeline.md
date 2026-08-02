# PRISMA Pipeline v1.0.0

## Status

`v1.0.0` is a calibration candidate. It becomes active only after the search
queries are frozen and the prompt suite passes both expert-gold accuracy and
five-run stability gates. The 2026-07-27 retrieval and all `v0.x` screening
outputs are superseded pilot evidence and are excluded from the final PRISMA
denominator.

Identification-source scope is amended by
`protocol/v1.1.2/search_scope_amendment.md`. In particular, Springer Nature is
excluded from identification and OpenAlex uses the scoped `v1.1.2` branch pack.

## 1. Identification

1. Calibrate database-native searches in PubMed, Scopus, Europe PMC, Semantic
   Scholar, Springer Nature, OpenAlex, and manual Google Scholar.
2. For every database combine aging and formal-causal-design blocks with
   either explicit multi-omics terminology or pairwise molecular-layer terms.
3. Review 50 records from each retrieval branch per database. Independently
   assess the 120-record prioritized candidate pool by two experts, adjudicate
   disagreements, and establish at least 100 eligible canonical positives.
   Run targeted supplemental retrieval for prespecified design families not
   represented in the initial pool.
4. Freeze query text, end date, API parameters, quality decisions, and Git
   commit before the complete retrieval.
5. Preserve each raw response, response hash, source count, normalized record,
   and query hash. Google Scholar is imported as a dated manual export.
6. Deduplicate conservatively by DOI, PMID/PMCID, and normalized bibliographic
   identity while retaining every source occurrence in the provenance log.

## 2. Title/abstract screening

Two independent prompt contracts are run five times with GPT 5.6 Terra Medium
through Codex CLI at `reasoning.effort=medium`:

- `scope_reviewer`: report type, biological scope, aging construct,
  multi-omics evidence, layer candidates, and current-report layer use;
- `causal_method_reviewer`: current-report attribution, one closed
  `causal_basis`, design families, causal-information sufficiency, and exact
  evidence spans.

Python validates schema, exact quoted substrings, and logical consistency. It
does not infer scientific meaning from keywords. A record is excluded only
when all five outputs identify the same first failed EC1-EC5 criterion.
`causal_wording_only`, `association_or_prediction_only`, and `none` support EC5
only when all five runs also call the causal information sufficient. Any
positive basis, `unclear`, thin abstract, invalid response after one retry, or
disagreement proceeds to full text. No model adjudicator, verifier prompt, or
directional-language route exists in v1.

## 3. Full-text assessment

Full-text sections receive stable IDs. A deterministic heading/keyword packager
selects and truncates sections under frozen character limits; no LLM section
selector is used. The eligibility and causal-evidence prompts each run five
times. Every evidence span must be a verbatim substring of its cited packaged
section.

Python assigns Levels 0-4 only when all decisive fields are unanimous and the
profile is sufficient. Disagreement, missing text, unsupported citations, or
an indeterminate grade is routed to human adjudication. Levels 2-4 enter the
synthesis; Level 2 is analyzed separately from Levels 3-4. Levels 0-1 remain
in the context/exclusion audit.

## 4. Gold-standard validation

Two experts independently annotate a 30-record codebook pilot. After
adjudication and codebook freeze, they independently annotate disjoint
80-record development and 100-record sealed title/abstract sets. A separate
60-paper full-text set covers Levels 0-4 and all design families. Prompt tuning
uses only the codebook and development sets. The sealed set is opened once
after Git freeze; a failed suite is rejected and the accessed set is never
reused for tuning.

Reports contain criterion-level confusion matrices, inter-rater agreement,
five-run disagreement, Wilson 95% intervals, unsupported evidence references,
and every human override. Passing stability without expert-gold validity is
not sufficient for activation.

## 5. Synthesis

The final PRISMA flow begins with the complete frozen v1 retrieval, not the
pilot. Study-level synthesis reports molecular layers, aging construct,
population/model, causal design family, estimand, assumptions, diagnostics,
validation, evidence level, and human adjudication status. Causal-hypothesis
and causal-evidence strata are never pooled as equivalent evidence.
