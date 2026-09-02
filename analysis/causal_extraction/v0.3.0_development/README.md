# Causal extraction v0.3 development analysis

This directory contains the pre-model analyst reference inventory for the 12
purposively sampled development reports.

## Status and interpretation

- `reference_inventory.json` is the manually assembled structured inventory.
- `reference_inventory_resolved.json` is a deterministic expansion in which
  every `evidence_atom_id` is resolved to exact Docling text and source metadata.
- The inventory contains 28 design-level causal analyses and 17 rejected
  boundary candidates supported by 232 atom references.
- No v0.3 Terra output had been generated or inspected when this draft was
  assembled.
- This is an AI-assisted analyst draft pending human verification. It is not an
  independent expert gold standard and cannot support a sealed accuracy claim.

The main granularity decision is to retain interventions, instruments, or
targeted perturbations as analysis units while treating genes, metabolites,
readouts, doses, time points, and strata as child contrasts when the identifying
design is unchanged. Correlation networks, enrichment, prediction,
colocalization alone, and untested mechanistic chains are recorded as rejected
candidates rather than causal analyses.

Validate IDs and regenerate the resolved view with:

```bash
.venv/bin/python scripts/validate_causal_extraction_v0_3_inventory.py --write-resolved
```
