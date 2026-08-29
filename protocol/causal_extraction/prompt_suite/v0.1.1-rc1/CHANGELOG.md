# Prompt suite v0.1.1-rc1 change log

## Basis

One v0.1.0-rc1 technical smoke window from checkpoint A returned 37 candidates, all labeled `association_link`. Six were ordinary genetic correlations and several were TWAS or age-expression associations outside the causal-claim extraction target. Seven evidence quotes also removed Markdown italic markers and failed exact substring validation. The API initially rejected the runtime schema before model execution; that separate compatibility problem was corrected in deterministic schema compilation.

Checkpoint B had no model calls before this version was frozen.

## Single conceptual ablation

- Require a named causal design, formal directed method, empirical operation, or formal causal-pipeline prioritization result for candidate nomination.
- Keep cautious `association` wording eligible when it reports an effect from a qualifying design such as Mendelian randomization.
- Move ordinary association, genetic correlation, differential expression, TWAS, colocalization-only, enrichment, prediction, and undirected network outputs to supporting evidence atoms.
- Remove `association_link` from the discovery candidate schema.
- Require character-exact copying of Markdown markers, Unicode symbols, whitespace, and punctuation.

No codebook, Level rule, coverage rule, model, reasoning effort, repeat count, or classifier/adjudicator prompt was changed.
