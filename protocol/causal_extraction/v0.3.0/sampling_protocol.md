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
