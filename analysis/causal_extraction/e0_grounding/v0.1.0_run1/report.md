# E0 deterministic grounding bake-off

Verdict: `technical_pass_pending_human_semantic_audit`.

This is a six-report development experiment. Every eligible report had prior Luna Light graph-profile exposure, so this result is not a sealed accuracy evaluation.

## Technical results

- Planned/terminal calls: 132/132.
- Complete atom coverage: 6/6 reports.
- `verbatim_quote` terminal validity: 66/66 (100.0%); first-attempt validity 62/66.
- `verbatim_quote` repeat agreement: all-field 15/33; decision-plus-grounding 17/33.
- `evidence_atom_id` terminal validity: 66/66 (100.0%); first-attempt validity 66/66.
- `evidence_atom_id` repeat agreement: all-field 15/33; decision-plus-grounding 15/33.
- Cross-arm agreement after Python atom resolution: all-field 30/66; decision-plus-grounding 31/66.
- Wilson intervals in `summary.json` are call- or reference-level technical descriptions; scientific uncertainty will be clustered by report.

## Audit status

A blinded 60-reference audit set and separate reviewer forms were generated locally. Two independent human judgments and adjudication remain pending. Until then, this experiment establishes technical resolvability only.

## Raw trace

The ignored raw run contains 1800 files (31169364 bytes). Its deterministic tree hash is `86545644a4a4a3759406008d100b6857af21ed767e1f39851b68f758d04d9ff9`. The accompanying JSON inventory records the path, byte size, and SHA-256 of every raw artifact.
