# Causal extraction methodology

## Current status

There is no active or production-approved causal-extraction codebook.

The `v0.1.0` and `v0.2.0` directories are historical instrument-development
artifacts. In particular, `v0.2.0` is a frozen, rejected pilot and must not be
used for:

- production causal extraction;
- Docling Graph template or schema generation;
- scientific synthesis or causal-level assignment;
- benchmark gold labels.

It may be used only to document instrument development and the methodological
postmortem. Its lifecycle marker is in `v0.2.0/lifecycle.json`.

The authoritative project state is recorded in `STATUS.md`. A replacement
hierarchical codebook is planned as `v0.3.0`, but it does not yet exist and is
not active.

## Historical lineage

| Version | Status | Permitted use |
|---|---|---|
| `v0.1.0` | historical pilot | instrument-development history only |
| `v0.2.0` | legacy, rejected, frozen | instrument-development history and methodological postmortem only |
| `v0.3.0` | planned, absent | none |

The decision to reject `v0.2.0` and redesign the unit of analysis is documented
in `design_decisions/2026-08-29-v0.1.1-failure-and-redesign.md`.
