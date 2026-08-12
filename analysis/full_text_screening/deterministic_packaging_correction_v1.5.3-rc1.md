# Deterministic Full-Text Packaging Correction v1.5.3-rc1

Date: 2026-08-12

## Decision

Full-text screening input must be selected and ordered deterministically. A
model-generated section selector, evidence graph, graph relation, or priority
flag must not influence which Docling chunks are supplied to a screening
reviewer.

The canonical `v1.4.0-rc1` scope and causal-method prompt templates remain
unchanged. The title/abstract evidence profile, schemas, scientific criteria,
five-repeat policy, and Python routing rules also remain unchanged.

## Deviation Found

Earlier full-text configurations assigned a score of `200` to chunks marked by
the Luna Light Docling Graph. This made a model-generated artifact part of the
section-ranking function. The graph was described as extraction provenance,
but it materially influenced reviewer input and therefore constituted an
additional AI retrieval stage.

Those runs are retained as superseded instrument-development pilots. They must
not be used as final PRISMA eligibility decisions or mixed with corrected
full-text results.

## Corrected Runtime Contract

Suite `v1.5.3-rc1`:

- assigns `graph_priority_score=0`;
- removes `graph_priority` from reviewer-visible section objects;
- ranks chunks only using versioned heading/text rules and original Docling
  chunk order for ties;
- records the selection method and omitted/truncated section IDs;
- routes unresolved or insufficient evidence to manual review;
- retains the same canonical criterion-level prompt templates.

Luna Light graph exports may remain archived as nondecision research
artifacts. They are not screening evidence and are not inputs to corrected
eligibility routing.

## PRISMA-trAIce Treatment

The graph-prioritized runs are reported as a protocol deviation and pilot under
M1, M3-M7, and D1. The corrected deterministic run is a new candidate
instrument and remains `calibration_pending_expert_gold`; stability alone does
not establish validity under M8-M9 and R2.
