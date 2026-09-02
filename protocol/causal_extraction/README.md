# Causal extraction methodology

## Current status

There is no active or production-approved causal-extraction instrument.

The `v0.1.0` and `v0.2.0` directories are historical instrument-development
artifacts. In particular, `v0.2.0` is a frozen, rejected pilot and must not be
used for:

- production causal extraction;
- Docling Graph template or schema generation;
- scientific synthesis or causal-level assignment;
- benchmark gold labels.

It may be used only to document instrument development and the methodological
postmortem. Its lifecycle marker is in `v0.2.0/lifecycle.json`.

The authoritative project state is recorded in `STATUS.md`. Version `v0.3.0`
is a frozen 12-report free-enumeration baseline. Its 60 Terra Medium calls were
valid, but only 1/12 reports reached exact agreement across five repeats. It is
therefore a failed development instrument and is not active for production.

Version `v0.3.1` fixed 45 candidate boundaries before classification. It
reached 45/45 five-repeat agreement for candidate qualification, while only
17/45 candidates reached exact agreement across all detailed fields. It is a
successful conditional-routing ablation and a failed complete-extraction
instrument. Automated discovery and detailed characterization remain open.

Version `v0.3.2` split the same fields across five role contracts. It reduced
five-repeat qualification agreement to 40/45 and complete candidate agreement
to 14/45. This negative ablation is frozen for reporting and must not replace
`v0.3.1` routing.

## Historical lineage

| Version | Status | Permitted use |
|---|---|---|
| `v0.1.0` | historical pilot | instrument-development history only |
| `v0.2.0` | legacy, rejected, frozen | instrument-development history and methodological postmortem only |
| `v0.3.0` | frozen failed development baseline | free-enumeration stability analysis and methodological postmortem only |
| `v0.3.1` | frozen conditional-routing ablation | fixed-candidate stability analysis only |
| `v0.3.2` | frozen failed role-contract ablation | stability analysis and methodological postmortem only |

The decision to reject `v0.2.0` and redesign the unit of analysis is documented
in `design_decisions/2026-08-29-v0.1.1-failure-and-redesign.md`. The `v0.3.0`
result and next one-factor ablation are documented in
`design_decisions/2026-09-02-v0.3.0-free-enumeration-failure.md`. Its outcome is
documented in `design_decisions/2026-09-02-v0.3.1-fixed-candidate-result.md`.
The role-contract outcome is documented in
`design_decisions/2026-09-02-v0.3.2-role-contract-result.md`.
