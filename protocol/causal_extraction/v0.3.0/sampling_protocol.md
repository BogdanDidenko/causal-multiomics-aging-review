# Causal extraction v0.3 development sample

Status: sample frozen before reference inventory, codebook finalization, and any
v0.3 Terra output.

## Purpose

This 12-report sample is used to define and test the `causal analysis` unit.
It is a development sample and cannot support sealed accuracy claims.

The reports were chosen by purposive maximum variation across anticipated
design family, biological system, aging construct, omics combination, document
structure, and difficult negative or mixed-method boundaries. Reports used in
causal-extraction checkpoint A, checkpoint B, or E0 were excluded.

Prior Luna graph profiles were already available for all 101 eligible reports.
Their broad categories were used as disclosed sampling cues. Their extracted
claims, evidence, and Levels are barred from the reference inventory.

## Evidence source

The source of record is the frozen deterministic full-text corpus used for
full-text eligibility screening. Python converts every canonical section into
stable `evidence-atoms-v1` records with exact offsets, raw text, and hashes.
No model selects, ranks, summarizes, or omits text during atomization.

The manual development inventory must cite `evidence_atom_id` values. Python
resolves those IDs back to exact text and rejects unknown IDs.

## Sequence

1. Freeze the 12-report sample and atom hashes.
2. Create the reference causal-analysis inventory from canonical text without
   viewing any v0.3 model output.
3. Freeze the short v0.3 codebook, schema, prompts, runtime, and metrics.
4. Run the fixed three-repeat and five-repeat policies on identical inputs.
5. Compare inventory recall, classification agreement, evidence grounding, and
   derived Levels. Keep the sample development-only.

The selection and source hashes are in `sample.json`. Rebuild and verify local
full-text evidence packets with:

```bash
.venv/bin/python scripts/freeze_causal_extraction_v0_3_sample.py --check
```

## Pre-model sample correction

The initial freeze included DOI `10.21037/tcr-2026-1-0264` as a
prediction-only boundary. During reference-inventory preparation, its local
source was found to contain only a four-page supplementary file (3,137
canonical characters), rather than the article body. Before any v0.3 model
output was generated, it was replaced with DOI
`10.1186/s40364-023-00458-9`, which has a complete article body and adds a
factorial genotype-by-diet-by-age design with an associational cross-omics
network boundary. The superseded packet is barred from v0.3 evaluation. This
correction and the new hashes are committed before codebook or prompt freeze.
