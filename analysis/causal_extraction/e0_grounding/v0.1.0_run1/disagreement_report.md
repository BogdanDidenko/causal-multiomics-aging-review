# E0 post-hoc disagreement audit

Status: exploratory post-hoc analysis of the frozen E0 run. The metrics below were not used to alter E0 prompts, schemas, runtime, or outputs.

## Main result

- `verbatim_quote`: full repeat agreement 15/33 (45.5%).
- `verbatim_quote` nonempty windows: full repeat agreement 0/18; analysis-count agreement 6/18; closed-field agreement 3/18.
- `evidence_atom_id`: full repeat agreement 15/33 (45.5%).
- `evidence_atom_id` nonempty windows: full repeat agreement 0/18; analysis-count agreement 7/18; closed-field agreement 4/18.

Every full exact repeat pair was an empty window. The grounding interface solved citation transport but did not localize the open scientific inventory task.

Across arms, nonempty full agreement was 0/36. This shows that changing the grounding output contract also changed upstream inventory behavior.

## Grounding result

The quote arm required 4 retries. All recorded first-attempt failures were character-exact substring failures caused by model-reproduced text. The evidence-ID arm required no retry and every returned ID resolved to frozen text.

## Boundary audit

Manual inspection of disagreement summaries identified three recurring boundary choices:

1. One perturbation was split by histology, molecular assay, or phenotype in one repeat and grouped as one experiment in another.
2. Multi-gene SMR estimates were represented as one screen in one repeat and as separate exposure-specific analyses in another.
3. The same experimental contrast received different design-family labels when transfer, intervention, and perturbation descriptions overlapped.

Representative audit locations were DOI `10.1038/s41413-025-00422-3`, window 002; DOI `10.1186/s12967-026-07766-2`, window 002; and DOI `10.1016/j.ccell.2024.09.002`, window 003. No article quotation is exported in this compact report.

## Decision

Retain `evidence_atom_id` for the next development instrument. Reject open window-level causal-analysis inventory. The next unit should be a design instance keyed by identifying variation or assignment, exposure, and biological system; outcomes and assay readouts should be child contrasts. Fixed atom-level role tagging should precede analysis assembly.

The two-human semantic audit and analysis-inventory gold remain pending. E0 therefore remains a technical result rather than an accuracy claim.
