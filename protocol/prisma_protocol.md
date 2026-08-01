# PRISMA Protocol

> **Superseded pilot.** This 2026-07-27 protocol is retained for audit only.
> The v1 candidate is `protocol/v1.0.0/prisma_pipeline.md`; this file must not
> define the final PRISMA denominator.

**Protocol version:** 0.1.0

**Initialized:** 2026-07-27

**Search end date:** 2026-07-27

**Lower date limit:** none
**Review type:** scoping review

## Identification

Run one frozen, database-native query in PubMed, Scopus, Europe PMC, Semantic
Scholar, Springer Nature, OpenAlex, and Google Scholar. The query has three
semantic blocks:

1. explicit multi-omics terminology;
2. explicit aging-process terminology;
3. broad causal-design anchors.

The third block is not limited to `causal inference` or `causal discovery`.
Google Scholar is a manual supplementary source because it has no official
API. Preserve source-native responses, query text, timestamps, API-reported
counts, retrieved counts, local validation counts, and errors.

PubMed and Europe PMC are the primary biomedical recall sources. Scopus uses a
multi-omics title anchor to improve precision. Semantic Scholar is a broad
title/abstract supplementary source. OpenAlex uses title plus
title/abstract filters. Springer Nature requires proximity constraints because
its accessible Meta API searches full text. The latter three sources require
post-retrieval title/abstract validation.

## Normalization and Deduplication

Normalize fields while retaining each source record and provenance. Collapse
exact DOI, PMID, PMCID, and normalized title/year matches. Link preprint and
published versions conservatively. Keep every merge decision in a
deduplication log and prefer the longest available abstract for screening.

## Selection

1. Validate query syntax and canonical-positive retrieval.
2. Build development and sealed holdout sets from the new aging corpus only.
3. Run independent scope/aging and causal-design reviewers.
4. Apply deterministic Python consistency and routing rules.
5. Adjudicate exclusions, uncertainty, and decisive conflicts.
6. Retrieve full text for retained or unresolved records.
7. Reassess eligibility, assumptions, diagnostics, validation, and evidence
   level at full text.
8. Link multiple reports of the same study before synthesis.

## Stability

All seven agent stages use `gpt-5.6-terra` through Codex CLI with
`reasoning.effort=medium`. Prompts request atomic criterion outputs, fixed
evaluation order, closed enums, shortest supporting spans, and no free-form
final decision. Five independent runs must show:

- 100% schema success after the one-retry policy;
- 100% exact agreement on every decisive criterion;
- 100% exact agreement on routing/final decision;
- 100% exact agreement on causal evidence level at full text;
- 0 unresolved manual-review records in the calibration set.

Failure localizes the disagreeing criterion and creates a new prompt version.
No calibration record may be added to the sealed holdout after inspection.

## Audit Requirements

Preserve the Git revision, input hash, query/prompt/schema/gate hashes,
model/provider, reasoning effort, timestamps, raw responses, parse errors,
criterion outputs, routing, exclusion codes, evidence spans, and human
overrides. Never edit an executed run or PRISMA denominator in place.
